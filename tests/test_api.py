"""API integration tests using TestClient (no real LLM/sandbox)."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_submit_rejects_non_csv() -> None:
    res = client.post(
        "/analyze",
        files={"file": ("data.txt", b"hello", "text/plain")},
        data={"question": "analyze"},
    )
    assert res.status_code == 400


def test_report_404_for_unknown_job() -> None:
    res = client.get("/analyze/report/does-not-exist")
    assert res.status_code == 404


@patch("api.routes.analysis._run_job", new_callable=AsyncMock)
def test_submit_returns_job_id(mock_run: AsyncMock) -> None:
    csv_content = b"a,b,c\n1,2,3\n4,5,6\n"
    res = client.post(
        "/analyze",
        files={"file": ("data.csv", io.BytesIO(csv_content), "text/csv")},
        data={"question": "test"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "job_id" in body
    assert body["stream_url"].startswith("/analyze/stream/")
    assert body["report_url"].startswith("/analyze/report/")
