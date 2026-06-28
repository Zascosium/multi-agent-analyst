"""Analysis endpoints: submit job, stream progress, fetch report."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from agents.graph import run_analysis
from api import jobs
from core.schemas import AnalyzeResponse

router = APIRouter(prefix="/analyze")


@router.post("", response_model=AnalyzeResponse)
async def submit_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question: str = Form(default="Give me a comprehensive analysis of this dataset."),
) -> AnalyzeResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    job_id = str(uuid.uuid4())
    csv_bytes = await file.read()
    jobs.create_job(job_id)

    background_tasks.add_task(
        _run_job, job_id=job_id, csv_bytes=csv_bytes, filename=file.filename, question=question
    )

    return AnalyzeResponse(
        job_id=job_id,
        stream_url=f"/analyze/stream/{job_id}",
        report_url=f"/analyze/report/{job_id}",
    )


@router.get("/stream/{job_id}")
async def stream_job(job_id: str) -> StreamingResponse:
    if not jobs.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in jobs.stream_events(job_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/report/{job_id}")
async def get_report(job_id: str) -> JSONResponse:
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "complete":
        raise HTTPException(status_code=202, detail=f"Job status: {job['status']}")

    state = job["state"]
    return JSONResponse(
        {
            "job_id": job_id,
            "report": state["report"],
            "charts": [
                {"title": c.title, "description": c.description, "image_b64": c.image_b64}
                for c in state.get("charts", [])
            ],
        }
    )


async def _run_job(job_id: str, csv_bytes: bytes, filename: str, question: str) -> None:
    await jobs.push_event(job_id, {"event": "agent_start", "agent": "orchestrator"})
    jobs.update_job(job_id, status="running")
    try:
        # run_analysis is synchronous (blocks on LLM + sandbox calls)
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None, lambda: run_analysis(csv_bytes, filename, job_id, question)
        )
        jobs.update_job(job_id, status="complete", state=final_state)
        await jobs.push_event(job_id, {"event": "complete", "agent": None})
    except Exception as exc:
        jobs.update_job(job_id, status="error", error=str(exc))
        await jobs.push_event(job_id, {"event": "error", "data": str(exc)})
