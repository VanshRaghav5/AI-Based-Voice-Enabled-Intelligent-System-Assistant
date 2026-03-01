from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config.logger import logger


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

