"""Runtime secret bootstrap utilities.

Ensures required security secrets exist for local desktop deployments
without requiring manual environment-variable setup on first run.
"""

import json
import os
import secrets
from pathlib import Path

from backend.config.logger import logger


REQUIRED_SECRET_KEYS = [
    "OMNIASSIST_FLASK_SECRET_KEY",
    "OMNIASSIST_JWT_SECRET",
]


def _secrets_file_path() -> Path:
    """Return local machine secrets file path (outside repo)."""
    base_dir = Path.home() / ".omniassist"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "secrets.json"


def _load_secret_file(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning(f"[Secrets] Failed to read secrets file: {exc}")
        return {}


def _write_secret_file(path: Path, payload: dict):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error(f"[Secrets] Failed to write secrets file: {exc}")


def ensure_runtime_secrets() -> dict:
    """Ensure required secrets exist in current process environment.

    Resolution order per key:
    1) Existing process environment variable
    2) Persisted local secrets file (~/.omniassist/secrets.json)
    3) New generated random value persisted to local secrets file
    """
    secrets_path = _secrets_file_path()
    persisted = _load_secret_file(secrets_path)
    changed = False
    resolved = {}

    for key in REQUIRED_SECRET_KEYS:
        value = os.environ.get(key, "").strip()
        if not value:
            value = str(persisted.get(key, "")).strip()

        if not value:
            # 64 chars random url-safe secret
            value = secrets.token_urlsafe(48)
            persisted[key] = value
            changed = True

        os.environ[key] = value
        resolved[key] = value

    if changed:
        _write_secret_file(secrets_path, persisted)
        logger.info(f"[Secrets] Generated local runtime secrets at: {secrets_path}")

    return resolved
