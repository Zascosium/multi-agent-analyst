"""Analyst agent: generates and self-heals pandas/numpy code."""

from __future__ import annotations

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings
from core.prompts import ANALYST_RETRY_SYSTEM, ANALYST_SYSTEM
from core.sandbox import SandboxRunner
from core.schemas import AnalysisState, CodeResult

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(model=settings.model, api_key=settings.anthropic_api_key)  # type: ignore[call-arg]


def analyst_node(state: AnalysisState, sandbox: SandboxRunner) -> dict:
    """LangGraph node: plan → write code → execute → retry on failure."""
    dataset_info = state["dataset_info"]
    assert dataset_info

    prompt = (
        f"Dataset: {dataset_info.filename} | shape: {dataset_info.shape}\n"
        f"Columns: {dataset_info.columns}\n"
        f"Dtypes: {dataset_info.dtypes}\n\n"
        f"Sample:\n{dataset_info.sample}\n\n"
        f"Numeric summary:\n{dataset_info.numeric_summary}\n\n"
        f"Analysis plan:\n{state['analysis_plan']}\n\n"
        f"User question: {state['user_question']}\n\n"
        "Write Python code to perform the statistical analysis described in the plan."
    )

    messages = [SystemMessage(content=ANALYST_SYSTEM), HumanMessage(content=prompt)]
    results: list[CodeResult] = []

    for attempt in range(1, settings.max_retries + 1):
        response = _llm.invoke(messages)
        code = _extract_code(str(response.content))
        result = sandbox.run(code, attempt=attempt)
        results.append(result)

        if result.success:
            logger.info("Analyst succeeded on attempt %d", attempt)
            break

        logger.warning("Analyst attempt %d failed, retrying...", attempt)
        retry_prompt = ANALYST_RETRY_SYSTEM.format(
            stderr=result.stderr, previous_code=code
        )
        messages = [
            SystemMessage(content=ANALYST_SYSTEM),
            HumanMessage(content=retry_prompt),
        ]

    return {
        "code_results": state.get("code_results", []) + results,
        "current_agent": "visualizer",
    }


def _extract_code(raw: str) -> str:
    """Strip markdown fences if the LLM wrapped the code anyway."""
    if "```" not in raw:
        return raw.strip()
    lines = raw.split("\n")
    inside = False
    code_lines: list[str] = []
    for line in lines:
        if line.startswith("```"):
            inside = not inside
            continue
        if inside:
            code_lines.append(line)
    return "\n".join(code_lines).strip()
