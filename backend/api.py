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
    """Return current assistant process state."""
    logger.info("[API] Status requested")
    status = "ACTIVE" if _is_assistant_running() else "IDLE"
    return StatusResponse(status=status, listening=True, message=None)


@app.post("/start", tags=["control"])
def start_assistant() -> dict:
    """Start the voice assistant process."""
    logger.info("[API] Start requested")
    if _is_assistant_running():
        return {"status": "ACTIVE", "message": "Assistant already running"}
    _start_assistant()
    return {"status": "ACTIVE", "message": "Assistant started"}


@app.post("/stop", tags=["control"])
def stop_assistant() -> dict:
    """Stop the voice assistant process."""
    logger.info("[API] Stop requested")
    if not _is_assistant_running():
        return {"status": "IDLE", "message": "Assistant not running"}
    _stop_assistant()
    return {"status": "IDLE", "message": "Assistant stopped"}

