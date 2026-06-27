"""In-process job store (swap for Redis-backed store in production)."""

from __future__ import annotations

import asyncio
from typing import Any

_jobs: dict[str, dict[str, Any]] = {}
_queues: dict[str, asyncio.Queue] = {}


def create_job(job_id: str) -> None:
    _jobs[job_id] = {"status": "pending", "state": None, "events": []}
    _queues[job_id] = asyncio.Queue()


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs: Any) -> None:
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)


async def push_event(job_id: str, event: dict[str, Any]) -> None:
    if job_id in _jobs:
        _jobs[job_id]["events"].append(event)
    if job_id in _queues:
        await _queues[job_id].put(event)


async def stream_events(job_id: str):
    """Async generator yielding events for SSE streaming."""
    queue = _queues.get(job_id)
    if not queue:
        return
    while True:
        event = await queue.get()
        yield event
        if event.get("event") in ("complete", "error"):
            break
