import os
import subprocess
import shutil
import urllib.request
from pathlib import Path
from typing import Optional

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

import ctypes

from backend.core.memory.memory_store import MemoryStore
from backend.core.memory.memory_manager import MemoryManager
from backend.tools.app_launcher import open_app as _open_app
from backend.tools.browser_control import open_url as _open_url
from backend.tools.browser_control import search_google as _search_google
from backend.tools.file_tools import create_file as _create_file
from backend.tools.file_tools import delete_file as _delete_file
from backend.tools.system_tools import shutdown_system as _shutdown_system
from backend.tools.system_tools import restart_system as _restart_system
from backend.utils.logger import logger


_memory_store = MemoryStore()
_memory_manager = MemoryManager()


def _normalize_result(result: dict) -> dict:
    if not isinstance(result, dict):
        return {"success": False, "error": "Invalid tool result"}

    if "success" in result:
        return result

    status = str(result.get("status", "")).lower()
    success = status == "success"
    merged = dict(result)
    merged["success"] = success
    if not success and "error" not in merged:
        merged["error"] = merged.get("message", "Tool execution failed")
    return merged


def open_app(app_name: str) -> dict:
    return _normalize_result(_open_app(app_name))


def close_app(app_name: str) -> dict:
    name = str(app_name or "").strip()
    if not name:
        return {"success": False, "status": "error", "error": "Application name is required"}

    image_name = name if name.lower().endswith(".exe") else f"{name}.exe"
    try:
        completed = subprocess.run(
            ["taskkill", "/F", "/IM", image_name],
            capture_output=True,
            text=True,
            shell=False,
        )
        ok = completed.returncode == 0
        return {
            "success": ok,
            "status": "success" if ok else "error",
            "message": f"Closed {image_name}" if ok else f"Could not close {image_name}",
            "error": "" if ok else (completed.stderr or completed.stdout or "Task kill failed"),
            "data": {"app_name": image_name},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Failed to close app"}


def get_running_apps(limit: int = 200) -> dict:
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            shell=False,
        )
        if completed.returncode != 0:
            return {
                "success": False,
                "status": "error",
                "error": completed.stderr or "Failed to list running apps",
            }

        rows = [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]
        apps = []
        for row in rows[: max(1, int(limit))]:
            cols = [c.strip().strip('"') for c in row.split('","')]
            if cols:
                apps.append(cols[0].strip('"'))

        return {
            "success": True,
            "status": "success",
            "message": f"Found {len(apps)} running apps",
            "data": {"apps": apps},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not get running apps"}


def set_volume(level: int) -> dict:
    try:
        target = max(0, min(100, int(level)))
        for _ in range(50):
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
        for _ in range(int(target / 2)):
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)

        return {
            "success": True,
            "status": "success",
            "message": f"Set volume to approximately {target}%",
            "data": {"level": target},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not set volume"}


def shutdown_system(confirm: bool = True) -> dict:
    return _normalize_result(_shutdown_system(confirm=confirm))


def restart_system(confirm: bool = True) -> dict:
    return _normalize_result(_restart_system(confirm=confirm))


def take_screenshot(filename: Optional[str] = None) -> dict:
    if ImageGrab is None:
        return {
            "success": False,
            "status": "error",
            "error": "Pillow ImageGrab is unavailable",
            "message": "Screenshot dependency not available",
        }

    try:
        output_name = str(filename or f"screenshot_{Path.cwd().name}.png").strip()
        if not output_name.lower().endswith(".png"):
            output_name = f"{output_name}.png"

        output_path = str(Path.home() / "Desktop" / output_name)
        image = ImageGrab.grab()
        image.save(output_path, "PNG")
        return {
            "success": True,
            "status": "success",
            "message": "Screenshot saved",
            "data": {"path": output_path},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not take screenshot"}


def run_command(command: str, cwd: Optional[str] = None, timeout: int = 120) -> dict:
    if not command or not str(command).strip():
        return {"success": False, "error": "Command cannot be empty"}

    workdir = cwd if cwd and os.path.isdir(cwd) else None

    try:
        completed = subprocess.run(
            command,
            cwd=workdir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout)),
        )

        ok = completed.returncode == 0
        message = "Command executed successfully" if ok else "Command failed"

        return {
            "success": ok,
            "status": "success" if ok else "error",
            "message": message,
            "error": "" if ok else (completed.stderr or f"Exit code {completed.returncode}"),
            "data": {
                "command": command,
                "cwd": workdir or os.getcwd(),
                "returncode": completed.returncode,
                "stdout": (completed.stdout or "").strip(),
                "stderr": (completed.stderr or "").strip(),
            },
        }
    except Exception as e:
        logger.error(f"[StarterTools] run_command failed: {e}")
        return {"success": False, "status": "error", "error": str(e), "message": "Command execution failed"}


def list_directory(path: str = ".") -> dict:
    try:
        target = Path(path).expanduser().resolve()
        if not target.exists() or not target.is_dir():
            return {
                "success": False,
                "status": "error",
                "error": "Directory not found",
                "message": f"Directory does not exist: {target}",
            }

        items = [p.name for p in sorted(target.iterdir(), key=lambda x: x.name.lower())]
        return {
            "success": True,
            "status": "success",
            "message": f"Listed {len(items)} items",
            "data": {"path": str(target), "items": items},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not list directory"}


def create_file(path: str) -> dict:
    return _normalize_result(_create_file(path))


def delete_file(path: str) -> dict:
    return _normalize_result(_delete_file(path))


def read_file(path: str, encoding: str = "utf-8") -> dict:
    try:
        target = Path(path).expanduser().resolve()
        if not target.exists() or not target.is_file():
            return {
                "success": False,
                "status": "error",
                "error": "File not found",
                "message": f"File not found: {target}",
            }

        content = target.read_text(encoding=encoding)
        return {
            "success": True,
            "status": "success",
            "message": "File read successfully",
            "data": {"path": str(target), "content": content},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not read file"}


def write_file(path: str, content: str, append: bool = False, encoding: str = "utf-8") -> dict:
    try:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with open(target, mode, encoding=encoding) as handle:
            handle.write(content or "")

        return {
            "success": True,
            "status": "success",
            "message": "File written successfully",
            "data": {"path": str(target), "append": bool(append)},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not write file"}


def move_file(source: str, destination: str) -> dict:
    try:
        src = Path(source).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()

        if not src.exists() or not src.is_file():
            return {
                "success": False,
                "status": "error",
                "error": "Source file not found",
                "message": f"Source file does not exist: {src}",
            }

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        return {
            "success": True,
            "status": "success",
            "message": "File moved successfully",
            "data": {"source": str(src), "destination": str(dst)},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Could not move file"}


def search_files(pattern: str, root: str = ".", max_results: int = 50) -> dict:
    if not pattern or not str(pattern).strip():
        return {"success": False, "status": "error", "error": "Pattern is required"}

    try:
        base = Path(root).expanduser().resolve()
        if not base.exists() or not base.is_dir():
            return {
                "success": False,
                "status": "error",
                "error": "Root directory not found",
                "message": f"Directory does not exist: {base}",
            }

        matches = []
        for match in base.rglob(pattern):
            matches.append(str(match))
            if len(matches) >= max(1, int(max_results)):
                break

        return {
            "success": True,
            "status": "success",
            "message": f"Found {len(matches)} files",
            "data": {"root": str(base), "pattern": pattern, "matches": matches},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "File search failed"}


def organize_folder(path: str, strategy: str = "extension") -> dict:
    target = Path(path or "").expanduser().resolve()
    if not target.exists() or not target.is_dir():
        return {
            "success": False,
            "status": "error",
            "error": "Folder not found",
            "message": f"Folder does not exist: {target}",
        }

    if strategy != "extension":
        return {
            "success": False,
            "status": "error",
            "error": "Unsupported strategy",
            "message": "Only 'extension' strategy is supported",
        }

    moved = 0
    errors = []
    for item in target.iterdir():
        if not item.is_file():
            continue

        ext = item.suffix.lower().lstrip(".") or "no_extension"
        destination_dir = target / ext
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / item.name
        try:
            shutil.move(str(item), str(destination))
            moved += 1
        except Exception as e:
            errors.append(f"{item.name}: {e}")

    success = len(errors) == 0
    return {
        "success": success,
        "status": "success" if success else "error",
        "message": f"Organized folder with {moved} files moved",
        "error": "" if success else "; ".join(errors[:5]),
        "data": {"path": str(target), "moved": moved, "errors": len(errors)},
    }


def _start_background_process(command: str, cwd: Optional[str] = None) -> dict:
    if not command or not str(command).strip():
        return {"success": False, "status": "error", "error": "Command cannot be empty"}

    try:
        workdir = cwd if cwd and os.path.isdir(cwd) else None
        process = subprocess.Popen(
            command,
            cwd=workdir,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "success": True,
            "status": "success",
            "message": "Process started",
            "data": {"pid": process.pid, "command": command, "cwd": workdir or os.getcwd()},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Failed to start process"}


def open_project(path: str) -> dict:
    project_path = str(Path(path or "").expanduser().resolve())
    if not os.path.isdir(project_path):
        return {"success": False, "status": "error", "error": f"Project path not found: {project_path}"}
    _memory_manager.set("project_path", project_path, persistent=True)
    _memory_manager.set("last_project", project_path)
    return _start_background_process(f'explorer "{project_path}"')


def run_backend_server(path: str = ".", command: str = "python -m backend.api_service") -> dict:
    return _start_background_process(command, cwd=str(Path(path).expanduser().resolve()))


def run_frontend(path: str = ".", command: str = "npm run dev") -> dict:
    return _start_background_process(command, cwd=str(Path(path).expanduser().resolve()))


def git_clone(repo_url: str, destination: str = ".") -> dict:
    url = str(repo_url or "").strip()
    if not url:
        return {"success": False, "status": "error", "error": "Repository URL is required"}
    return run_command(f'git clone "{url}" "{destination}"')


def git_pull(path: str = ".") -> dict:
    return run_command("git pull", cwd=str(Path(path).expanduser().resolve()))


def git_push(path: str = ".") -> dict:
    return run_command("git push", cwd=str(Path(path).expanduser().resolve()))


def install_dependencies(path: str = ".") -> dict:
    project = Path(path).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        return {
            "success": False,
            "status": "error",
            "error": f"Path does not exist: {project}",
            "message": "Invalid project path",
        }

    if (project / "requirements.txt").exists() or (project / "requirements-test.txt").exists():
        req_file = "requirements.txt" if (project / "requirements.txt").exists() else "requirements-test.txt"
        return run_command(f"pip install -r {req_file}", cwd=str(project), timeout=600)
    if (project / "package.json").exists():
        return run_command("npm install", cwd=str(project), timeout=600)

    return {
        "success": False,
        "status": "error",
        "error": "No supported dependency manifest found",
        "message": "Expected requirements.txt or package.json",
    }


def open_url(url: str) -> dict:
    return _normalize_result(_open_url(url))


def search_google(query: str) -> dict:
    return _normalize_result(_search_google(query))


def search_youtube(query: str) -> dict:
    cleaned = str(query or "").strip()
    if not cleaned:
        return {"success": False, "status": "error", "error": "Query is required"}

    url = f"https://www.youtube.com/results?search_query={cleaned.replace(' ', '+')}"
    return open_url(url)


def download_file(url: str, destination: str) -> dict:
    cleaned_url = str(url or "").strip()
    dest = Path(destination or "").expanduser().resolve()
    if not cleaned_url:
        return {"success": False, "status": "error", "error": "URL is required"}
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        urllib.request.urlretrieve(cleaned_url, str(dest))
        return {
            "success": True,
            "status": "success",
            "message": "File downloaded",
            "data": {"url": cleaned_url, "path": str(dest)},
        }
    except Exception as e:
        return {"success": False, "status": "error", "error": str(e), "message": "Download failed"}


def remember_data(key: str, value: str) -> dict:
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return {"success": False, "status": "error", "error": "Memory key is required"}

    saved_value = str(value or "")
    _memory_manager.set(normalized_key, saved_value, persistent=True)
    ok = _memory_store.remember_fact(normalized_key, saved_value)
    if not ok:
        return {"success": False, "status": "error", "error": "Could not store memory"}

    return {
        "success": True,
        "status": "success",
        "message": f"Stored memory for key '{normalized_key}'",
        "data": {"key": normalized_key},
    }


def recall_data(key: str) -> dict:
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return {"success": False, "status": "error", "error": "Memory key is required"}

    value = _memory_manager.get(normalized_key)
    if value is None:
        value = _memory_store.recall_fact(normalized_key)
    if value is None:
        return {
            "success": False,
            "status": "error",
            "error": "Memory not found",
            "message": f"No memory found for key '{normalized_key}'",
        }

    return {
        "success": True,
        "status": "success",
        "message": "Memory recalled",
        "data": {"key": normalized_key, "value": value},
    }


def delete_memory(key: str) -> dict:
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return {"success": False, "status": "error", "error": "Memory key is required"}

    removed = _memory_store.forget_fact(normalized_key)
    _memory_manager.delete(normalized_key, persistent=True)
    _memory_manager.delete(normalized_key, persistent=False)
    if not removed:
        return {
            "success": False,
            "status": "error",
            "error": "Memory key not found",
            "message": f"No memory found for key '{normalized_key}'",
        }

    return {
        "success": True,
        "status": "success",
        "message": f"Deleted memory for key '{normalized_key}'",
        "data": {"key": normalized_key},
    }


def list_memory() -> dict:
    facts = _memory_store.list_facts()
    long_term_facts = _memory_manager.get_context().get("long_term", {})
    merged_facts = dict(long_term_facts)
    merged_facts.update(facts)
    return {
        "success": True,
        "status": "success",
        "message": f"Listed {len(merged_facts)} memory items",
        "data": {"facts": merged_facts},
    }
