"""Unit tests for agent utilities (no real LLM or sandbox calls)."""

from __future__ import annotations

import pytest

from agents.analyst import _extract_code


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("print('hello')", "print('hello')"),
        ("```python\nprint('hello')\n```", "print('hello')"),
        ("```\ndf.describe()\n```", "df.describe()"),
    ],
)
def test_extract_code(raw: str, expected: str) -> None:
    assert _extract_code(raw) == expected
