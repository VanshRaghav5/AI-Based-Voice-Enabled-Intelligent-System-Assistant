from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config.logger import logger

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
assistant_process: subprocess.Popen | None = None


class StatusResponse(BaseModel):
    """Basic status model returned to the desktop UI."""

    status: str
    listening: bool = True
    message: str | None = None


app = FastAPI(title="AI Voice Assistant API")

# Allow Electron renderer to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_assistant_running() -> bool:
    return assistant_process is not None and assistant_process.poll() is None


def _start_assistant() -> None:
    global assistant_process
    if _is_assistant_running():
        return

    # Use current Python and run the root app.py from project root
    cmd = [sys.executable, "app.py"]
    assistant_process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))


def _stop_assistant() -> None:
    global assistant_process
    if not _is_assistant_running():
        return

    assistant_process.terminate()
    try:
        assistant_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        assistant_process.kill()
    assistant_process = None


@app.get("/", tags=["health"])
def root_health() -> dict:
    """Simple health check endpoint."""
    logger.info("[API] Health check requested")
    return {"ok": True}


@app.get("/status", response_model=StatusResponse, tags=["status"])
def get_status() -> StatusResponse:
    """
    Initial /status implementation.

    For now this is static (IDLE + listening=True). In later steps
    we'll wire this up to the real assistant process state.
    """
    logger.info("[API] Status requested")
    return StatusResponse(status="IDLE", listening=True, message=None)

