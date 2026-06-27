from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class DatasetInfo(BaseModel):
    filename: str
    shape: tuple[int, int]
    columns: list[str]
    dtypes: dict[str, str]
    sample: str  # string repr of df.head()
    numeric_summary: str  # string repr of df.describe()


class CodeResult(BaseModel):
    code: str
    stdout: str
    stderr: str
    success: bool
    attempt: int = 1


class Chart(BaseModel):
    title: str
    description: str
    image_b64: str  # base64-encoded PNG


class AnalysisState(TypedDict):
    """Shared state flowing through the LangGraph agent graph."""

    messages: Annotated[list[Any], add_messages]
    job_id: str
    user_question: str
    dataset_info: DatasetInfo | None
    analysis_plan: str
    code_results: list[CodeResult]
    charts: list[Chart]
    report: str
    error: str | None
    current_agent: str


class AnalyzeRequest(BaseModel):
    question: str = Field(
        default="Give me a comprehensive analysis of this dataset.",
        description="The analysis question or goal.",
    )


class AnalyzeResponse(BaseModel):
    job_id: str
    stream_url: str
    report_url: str


class StreamEvent(BaseModel):
    event: str  # "agent_start" | "agent_output" | "complete" | "error"
    agent: str | None = None
    data: Any = None
