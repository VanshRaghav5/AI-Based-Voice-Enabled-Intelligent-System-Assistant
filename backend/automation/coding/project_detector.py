# backend/automation/coding/project_detector.py

import os
import glob
from typing import Dict, Any, Optional

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


# Detection matrix mapping marker files to project metadata.
_PROJECT_SIGNATURES = [
    {
        "marker": "package.json",
        "project_type": "node",
        "language": "javascript",
        "package_manager": "npm",
        "install_command": "npm install",
        "run_command": "npm run dev",
        "lockfiles": {
            "yarn.lock": ("yarn", "yarn install", "yarn dev"),
            "pnpm-lock.yaml": ("pnpm", "pnpm install", "pnpm dev"),
            "bun.lockb": ("bun", "bun install", "bun dev"),
        },
    },
    {
        "marker": "requirements.txt",
        "project_type": "python",
        "language": "python",
        "package_manager": "pip",
        "install_command": "pip install -r requirements.txt",
        "run_command": "python main.py",
    },
    {
        "marker": "pyproject.toml",
        "project_type": "python",
        "language": "python",
        "package_manager": "pip",
        "install_command": "pip install -e .",
        "run_command": "python -m app",
    },
    {
        "marker": "Cargo.toml",
        "project_type": "rust",
        "language": "rust",
        "package_manager": "cargo",
        "install_command": "cargo build",
        "run_command": "cargo run",
    },
    {
        "marker": "go.mod",
        "project_type": "go",
        "language": "go",
        "package_manager": "go",
        "install_command": "go mod download",
        "run_command": "go run .",
    },
    {
        "marker": "pom.xml",
        "project_type": "java",
        "language": "java",
        "package_manager": "maven",
        "install_command": "mvn install",
        "run_command": "mvn exec:java",
    },
    {
        "marker": "build.gradle",
        "project_type": "java",
        "language": "java",
        "package_manager": "gradle",
        "install_command": "gradle build",
        "run_command": "gradle run",
    },
    {
        "marker": "Gemfile",
        "project_type": "ruby",
        "language": "ruby",
        "package_manager": "bundler",
        "install_command": "bundle install",
        "run_command": "bundle exec ruby app.rb",
    },
    {
        "marker": "Makefile",
        "project_type": "make",
        "language": "varies",
        "package_manager": "make",
        "install_command": "make",
        "run_command": "make run",
    },
    {
        "marker": "docker-compose.yml",
        "project_type": "docker",
        "language": "varies",
        "package_manager": "docker",
        "install_command": "docker compose build",
        "run_command": "docker compose up",
    },
    {
        "marker": "docker-compose.yaml",
        "project_type": "docker",
        "language": "varies",
        "package_manager": "docker",
        "install_command": "docker compose build",
        "run_command": "docker compose up",
    },
]


def _detect_dotnet(root: str) -> Optional[Dict[str, Any]]:
    """Check for .NET projects (.sln or .csproj files)."""
    for pattern in ("*.sln", "*.csproj"):
        matches = glob.glob(os.path.join(root, pattern))
        if matches:
            return {
                "project_type": "dotnet",
                "language": "csharp",
                "package_manager": "dotnet",
                "dependency_file": os.path.basename(matches[0]),
                "install_command": "dotnet restore",
                "run_command": "dotnet run",
            }
    return None


def detect_project(path: str) -> Dict[str, Any]:
    """Analyse *path* and return project metadata.

    Returns a dict with keys:
        project_type, language, package_manager, dependency_file,
        install_command, run_command, has_lockfile, has_env_template,
        has_git, detected_files
    """
    root = os.path.abspath(path)

    if not os.path.isdir(root):
        raise AutomationError(
            f"Path is not a directory: {root}",
            f"I could not find a project folder at {root}.",
        )

    entries = set(os.listdir(root))
    detected_files = sorted(entries)

    # --- Try signature-based detection ---
    for sig in _PROJECT_SIGNATURES:
        if sig["marker"] not in entries:
            continue

        info: Dict[str, Any] = {
            "project_type": sig["project_type"],
            "language": sig["language"],
            "package_manager": sig["package_manager"],
            "dependency_file": sig["marker"],
            "install_command": sig["install_command"],
            "run_command": sig["run_command"],
            "has_lockfile": False,
        }

        # Check for alternative lockfile-based package managers (Node.js).
        lockfiles = sig.get("lockfiles", {})
        for lockfile, (pm, install_cmd, run_cmd) in lockfiles.items():
            if lockfile in entries:
                info["package_manager"] = pm
                info["install_command"] = install_cmd
                info["run_command"] = run_cmd
                info["has_lockfile"] = True
                break

        if not info["has_lockfile"]:
            # Check for default lockfiles (package-lock.json, Cargo.lock, etc.)
            common_locks = [
                "package-lock.json", "Cargo.lock", "go.sum",
                "Gemfile.lock", "poetry.lock",
            ]
            info["has_lockfile"] = any(lf in entries for lf in common_locks)

        info["has_env_template"] = ".env.example" in entries or ".env.sample" in entries
        info["has_git"] = ".git" in entries
        info["detected_files"] = detected_files

        # Refine Node.js language detection (TypeScript).
        if sig["project_type"] == "node" and "tsconfig.json" in entries:
            info["language"] = "typescript"

        # Refine Python: prefer poetry if pyproject.toml with poetry.lock.
        if sig["marker"] == "pyproject.toml" and "poetry.lock" in entries:
            info["package_manager"] = "poetry"
            info["install_command"] = "poetry install"
            info["run_command"] = "poetry run python -m app"

        logger.info(f"[ProjectDetector] Detected {info['project_type']} project at {root}")
        return info

    # --- Try .NET detection ---
    dotnet_info = _detect_dotnet(root)
    if dotnet_info:
        dotnet_info["has_lockfile"] = False
        dotnet_info["has_env_template"] = ".env.example" in entries or ".env.sample" in entries
        dotnet_info["has_git"] = ".git" in entries
        dotnet_info["detected_files"] = detected_files
        logger.info(f"[ProjectDetector] Detected dotnet project at {root}")
        return dotnet_info

    # --- Unknown project ---
    logger.warning(f"[ProjectDetector] Could not identify project type at {root}")
    return {
        "project_type": "unknown",
        "language": "unknown",
        "package_manager": "unknown",
        "dependency_file": "",
        "install_command": "",
        "run_command": "",
        "has_lockfile": False,
        "has_env_template": ".env.example" in entries or ".env.sample" in entries,
        "has_git": ".git" in entries,
        "detected_files": detected_files,
    }


class ProjectDetectorTool(BaseTool):
    name = "code.detect_project"
    description = "Detect project type, language, and setup requirements for a directory"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, path: str = ".") -> Dict[str, Any]:
        resolved = os.path.abspath(path)

        def _detect():
            info = detect_project(resolved)
            project_type = info.get("project_type", "unknown")
            install_cmd = info.get("install_command", "")
            run_cmd = info.get("run_command", "")

            summary_parts = [f"Detected a {project_type} project"]
            if install_cmd:
                summary_parts.append(f"install with: {install_cmd}")
            if run_cmd:
                summary_parts.append(f"run with: {run_cmd}")

            return {
                "status": "success",
                "message": ". ".join(summary_parts),
                "data": info,
            }

        return error_handler.wrap_automation(
            func=_detect,
            operation_name="Detect Project",
            context={"path": resolved},
        )
