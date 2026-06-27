"""Visualizer agent: generates matplotlib charts from analysis results."""

from __future__ import annotations

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings
from core.prompts import VISUALIZER_SYSTEM
from core.sandbox import SandboxRunner
from core.schemas import AnalysisState, Chart

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(model=settings.model, api_key=settings.anthropic_api_key)  # type: ignore[call-arg]

_MAX_CHARTS = 5


def visualizer_node(state: AnalysisState, sandbox: SandboxRunner) -> dict:
    """LangGraph node: determine charts → generate code → execute → collect images."""
    dataset_info = state["dataset_info"]
    assert dataset_info

    analysis_summary = "\n\n".join(
        f"[Attempt {r.attempt}]\n{r.stdout}" for r in state["code_results"] if r.success
    )

    prompt = (
        f"Dataset columns: {dataset_info.columns}\n"
        f"Dtypes: {dataset_info.dtypes}\n\n"
        f"Analysis plan:\n{state['analysis_plan']}\n\n"
        f"Analysis results:\n{analysis_summary}\n\n"
        f"Create up to {_MAX_CHARTS} insightful matplotlib visualizations. "
        "For EACH chart, return a JSON object on a single line with keys: "
        '"title", "description", "code". '
        "Output one JSON object per line, nothing else."
    )

    response = _llm.invoke(
        [SystemMessage(content=VISUALIZER_SYSTEM), HumanMessage(content=prompt)]
    )

    charts: list[Chart] = []
    for line in str(response.content).strip().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            import json

            spec = json.loads(line)
            chart = sandbox.run_chart(
                code=spec["code"],
                title=spec.get("title", "Chart"),
                description=spec.get("description", ""),
            )
            if chart:
                charts.append(chart)
        except Exception as exc:
            logger.warning("Failed to generate chart: %s", exc)

    logger.info("Visualizer produced %d charts", len(charts))
    return {"charts": charts, "current_agent": "writer"}
