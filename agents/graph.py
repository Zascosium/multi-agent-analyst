"""LangGraph state machine wiring all agents together."""

from __future__ import annotations

import io
import logging

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from agents.analyst import analyst_node
from agents.visualizer import visualizer_node
from agents.writer import writer_node
from core.config import settings
from core.prompts import ORCHESTRATOR_SYSTEM
from core.sandbox import SandboxRunner
from core.schemas import AnalysisState, DatasetInfo

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(model=settings.model, api_key=settings.anthropic_api_key)  # type: ignore[call-arg]


def _parse_dataset(csv_bytes: bytes, filename: str) -> DatasetInfo:
    df = pd.read_csv(io.BytesIO(csv_bytes))
    return DatasetInfo(
        filename=filename,
        shape=df.shape,
        columns=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        sample=df.head(5).to_string(),
        numeric_summary=df.describe().to_string(),
    )


def _orchestrator_node(state: AnalysisState) -> dict:
    dataset_info = state["dataset_info"]
    assert dataset_info
    prompt = (
        f"Dataset: {dataset_info.filename} | shape: {dataset_info.shape}\n"
        f"Columns: {dataset_info.columns}\n"
        f"Dtypes: {dataset_info.dtypes}\n\n"
        f"Sample:\n{dataset_info.sample}\n\n"
        f"Numeric summary:\n{dataset_info.numeric_summary}\n\n"
        f"User question: {state['user_question']}\n\n"
        "Create the analysis plan."
    )
    response = _llm.invoke(
        [SystemMessage(content=ORCHESTRATOR_SYSTEM), HumanMessage(content=prompt)]
    )
    logger.info("Orchestrator produced plan")
    return {"analysis_plan": str(response.content), "current_agent": "analyst"}


def _route(state: AnalysisState) -> str:
    return state.get("current_agent", "done")


def build_graph(sandbox: SandboxRunner) -> StateGraph:
    builder = StateGraph(AnalysisState)
    builder.add_node("orchestrator", _orchestrator_node)

    # Analyst and visualizer need access to the shared sandbox.
    builder.add_node("analyst", lambda s: analyst_node(s, sandbox))
    builder.add_node("visualizer", lambda s: visualizer_node(s, sandbox))
    builder.add_node("writer", writer_node)

    builder.set_entry_point("orchestrator")
    builder.add_conditional_edges("orchestrator", _route)
    builder.add_conditional_edges("analyst", _route)
    builder.add_conditional_edges("visualizer", _route)
    builder.add_edge("writer", END)

    return builder


def run_analysis(
    csv_bytes: bytes,
    filename: str,
    job_id: str,
    question: str = "Give me a comprehensive analysis of this dataset.",
) -> AnalysisState:
    """Entry point: parses CSV, runs the full agent graph, returns final state."""
    dataset_info = _parse_dataset(csv_bytes, filename)

    initial_state: AnalysisState = {
        "messages": [],
        "job_id": job_id,
        "user_question": question,
        "dataset_info": dataset_info,
        "analysis_plan": "",
        "code_results": [],
        "charts": [],
        "report": "",
        "error": None,
        "current_agent": "orchestrator",
    }

    with SandboxRunner() as sandbox:
        # Upload CSV once; all agents share the same sandbox session
        csv_path = sandbox.upload_csv(csv_bytes, filename)
        init_code = f"import pandas as pd\ndf = pd.read_csv('{csv_path}')"
        sandbox.run(init_code)

        graph = build_graph(sandbox)
        app = graph.compile()

        final_state: AnalysisState = app.invoke(initial_state)  # type: ignore[assignment]

    return final_state
