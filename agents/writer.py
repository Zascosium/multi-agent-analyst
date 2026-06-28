"""Writer agent: synthesizes all results into a Markdown report."""

from __future__ import annotations

import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from core.config import settings
from core.prompts import WRITER_SYSTEM
from core.schemas import AnalysisState

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(model=settings.model, api_key=SecretStr(settings.anthropic_api_key))  # type: ignore[call-arg]


def writer_node(state: AnalysisState) -> dict[str, Any]:
    """LangGraph node: synthesize all findings into a structured report."""
    dataset_info = state["dataset_info"]
    assert dataset_info

    analysis_outputs = "\n\n".join(
        f"[Code attempt {r.attempt}]\n```\n{r.stdout}\n```"
        for r in state["code_results"]
        if r.success
    )

    chart_descriptions = "\n".join(
        f"chart:{i} — {c.title}: {c.description}"
        for i, c in enumerate(state.get("charts", []))
    )

    prompt = (
        f"Dataset: {dataset_info.filename} ({dataset_info.shape[0]} rows, "
        f"{dataset_info.shape[1]} columns)\n\n"
        f"User question: {state['user_question']}\n\n"
        f"Analysis plan:\n{state['analysis_plan']}\n\n"
        f"Analysis outputs:\n{analysis_outputs}\n\n"
        f"Available charts:\n{chart_descriptions}\n\n"
        "Write the full analysis report now."
    )

    response = _llm.invoke(
        [SystemMessage(content=WRITER_SYSTEM), HumanMessage(content=prompt)]
    )

    logger.info("Writer completed report (%d chars)", len(str(response.content)))
    return {"report": str(response.content), "current_agent": "done"}
