from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DesktopConfig:
    base_url: str
    socket_url: str


def load_config() -> DesktopConfig:
    """Load desktop configuration.

    Configuration sources:
    - Env var `OMNIASSIST_BASE_URL` (default: http://127.0.0.1:5000)
    - Env var `OMNIASSIST_SOCKET_URL` (default: base url)
    """

    base_url = os.getenv("OMNIASSIST_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    socket_url = os.getenv("OMNIASSIST_SOCKET_URL", base_url).rstrip("/")
    return DesktopConfig(base_url=base_url, socket_url=socket_url)
