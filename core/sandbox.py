"""E2B sandbox wrapper for safe LLM-generated code execution."""

from __future__ import annotations

import base64
import logging

from e2b_code_interpreter import Sandbox

from core.config import settings
from core.schemas import Chart, CodeResult

logger = logging.getLogger(__name__)

_MATPLOTLIB_SAVE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

def _save_current_fig(title="chart"):
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    plt.close('all')
    return encoded
"""


class SandboxRunner:
    """Manages an E2B sandbox session for one analysis job."""

    def __init__(self) -> None:
        self._sandbox: Sandbox | None = None

    def __enter__(self) -> "SandboxRunner":
        self._sandbox = Sandbox(
            api_key=settings.e2b_api_key,
            timeout=settings.sandbox_timeout,
        )
        # Pre-install common analysis libs and inject chart helper
        self._sandbox.run_code("import pandas as pd, numpy as np, matplotlib, plotly")
        self._sandbox.run_code(_MATPLOTLIB_SAVE)
        return self

    def __exit__(self, *_: object) -> None:
        if self._sandbox:
            try:
                self._sandbox.kill()
            except Exception:
                pass

    def run(self, code: str, attempt: int = 1) -> CodeResult:
        assert self._sandbox, "SandboxRunner must be used as a context manager"
        try:
            execution = self._sandbox.run_code(code)
            stdout = "\n".join(str(r) for r in execution.results if r)
            logs = execution.logs
            stderr = "\n".join(logs.stderr) if logs.stderr else ""
            success = not execution.error
            if execution.error:
                stderr = f"{execution.error.name}: {execution.error.value}\n{stderr}"
            logger.debug("Sandbox run attempt=%d success=%s", attempt, success)
            return CodeResult(
                code=code, stdout=stdout, stderr=stderr, success=success, attempt=attempt
            )
        except Exception as exc:
            return CodeResult(
                code=code,
                stdout="",
                stderr=str(exc),
                success=False,
                attempt=attempt,
            )

    def run_chart(self, code: str, title: str, description: str) -> Chart | None:
        """Execute chart code and capture the figure as base64 PNG."""
        capture_code = code + "\n_img = _save_current_fig()\nprint(_img)"
        result = self.run(capture_code)
        if not result.success or not result.stdout.strip():
            logger.warning("Chart generation failed: %s", result.stderr)
            return None
        return Chart(title=title, description=description, image_b64=result.stdout.strip())

    def upload_csv(self, csv_bytes: bytes, filename: str) -> str:
        """Write CSV into the sandbox and return the path."""
        assert self._sandbox
        path = f"/home/user/{filename}"
        self._sandbox.files.write(path, csv_bytes)
        return path
