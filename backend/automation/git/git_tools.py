# backend/automation/git/git_tools.py
#
# All tools shell out to the local ``git`` CLI via subprocess.
# No API calls, no OAuth, no REST — just plain git commands.

import os
import re
import shutil
import subprocess
from typing import Dict, Any, List

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_git() -> str:
    """Return the path to the git binary or raise."""
    git_path = shutil.which("git")
    if git_path:
        return git_path
    raise AutomationError(
        "git not found on PATH",
        "I could not find git. Please install Git and make sure it is on your PATH.",
    )


def _run_git(args: List[str], cwd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a git command and return the CompletedProcess result."""
    git = _find_git()
    cmd = [git, "-C", cwd] + args
    logger.info(f"[Git] Running: {' '.join(cmd)}")
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AutomationError(
            f"Git command timed out after {timeout}s",
            "The git command took too long. Please try again.",
        )
    except Exception as exc:
        raise AutomationError(str(exc), f"Failed to run git command: {exc}")


def _ensure_git_repo(cwd: str) -> None:
    """Verify *cwd* is inside a git repository."""
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd, timeout=5)
    if result.returncode != 0:
        raise AutomationError(
            f"Not a git repository: {cwd}",
            f"The directory {cwd} is not a git repository. Run 'git init' first.",
        )


# ===================================================================
# Tool: git.status
# ===================================================================

class GitStatusTool(BaseTool):
    name = "git.status"
    description = "Show git status of a project"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, cwd: str = ".") -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _status():
            _ensure_git_repo(resolved)
            result = _run_git(["status", "--porcelain"], resolved)

            modified = []
            untracked = []
            staged = []

            for line in result.stdout.strip().splitlines():
                if len(line) < 3:
                    continue
                index_flag = line[0]
                worktree_flag = line[1]
                filepath = line[3:].strip()

                if index_flag in ("A", "M", "D", "R"):
                    staged.append(filepath)
                if worktree_flag == "M":
                    modified.append(filepath)
                if index_flag == "?" and worktree_flag == "?":
                    untracked.append(filepath)

            total = len(staged) + len(modified) + len(untracked)
            if total == 0:
                msg = "Working tree is clean — nothing to commit."
            else:
                parts = []
                if staged:
                    parts.append(f"{len(staged)} staged")
                if modified:
                    parts.append(f"{len(modified)} modified")
                if untracked:
                    parts.append(f"{len(untracked)} untracked")
                msg = f"Git status: {', '.join(parts)} file(s)."

            return {
                "status": "success",
                "message": msg,
                "data": {
                    "staged": staged,
                    "modified": modified,
                    "untracked": untracked,
                    "cwd": resolved,
                },
            }

        return error_handler.wrap_automation(
            func=_status,
            operation_name="Git Status",
            context={"cwd": resolved},
        )


# ===================================================================
# Tool: git.add
# ===================================================================

class GitAddTool(BaseTool):
    name = "git.add"
    description = "Stage files for git commit"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, cwd: str = ".", files: str = ".") -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _add():
            _ensure_git_repo(resolved)

            # Split files string into list if space-separated.
            file_args = files.strip().split() if files and files.strip() else ["."]
            result = _run_git(["add"] + file_args, resolved)

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown git add error"
                raise AutomationError(error_msg, f"Failed to stage files: {error_msg}")

            label = "all files" if files.strip() == "." else files.strip()
            return {
                "status": "success",
                "message": f"Staged {label} for commit.",
                "data": {"files": file_args, "cwd": resolved},
            }

        return error_handler.wrap_automation(
            func=_add,
            operation_name="Git Add",
            context={"cwd": resolved, "files": files},
        )


# ===================================================================
# Tool: git.commit
# ===================================================================

class GitCommitTool(BaseTool):
    name = "git.commit"
    description = "Commit staged changes with a message"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, message: str, cwd: str = ".") -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _commit():
            _ensure_git_repo(resolved)

            commit_msg = (message or "").strip()
            if not commit_msg:
                commit_msg = "update"

            result = _run_git(["commit", "-m", commit_msg], resolved)

            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "nothing to commit" in stderr or "nothing to commit" in (result.stdout or ""):
                    return {
                        "status": "success",
                        "message": "Nothing to commit — working tree is clean.",
                        "data": {"cwd": resolved},
                    }
                raise AutomationError(stderr or "Commit failed", f"Git commit failed: {stderr}")

            # Parse commit hash from output like "[branch abc1234] message"
            commit_hash = ""
            stdout = result.stdout.strip()
            hash_match = re.search(r"\[[\w/.-]+\s+([a-f0-9]+)\]", stdout)
            if hash_match:
                commit_hash = hash_match.group(1)

            # Count files changed from summary line.
            files_changed = 0
            changed_match = re.search(r"(\d+)\s+file", stdout)
            if changed_match:
                files_changed = int(changed_match.group(1))

            return {
                "status": "success",
                "message": f"Committed: {commit_msg} ({commit_hash})",
                "data": {
                    "commit_hash": commit_hash,
                    "message": commit_msg,
                    "files_changed": files_changed,
                    "cwd": resolved,
                },
            }

        return error_handler.wrap_automation(
            func=_commit,
            operation_name="Git Commit",
            context={"cwd": resolved, "message": message},
        )


# ===================================================================
# Tool: git.push
# ===================================================================

class GitPushTool(BaseTool):
    name = "git.push"
    description = "Push commits to remote repository"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self, cwd: str = ".", remote: str = "origin", branch: str = "") -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _push():
            _ensure_git_repo(resolved)

            push_args = ["push", remote]
            if branch and branch.strip():
                push_args.append(branch.strip())

            result = _run_git(push_args, resolved, timeout=60)

            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise AutomationError(
                    stderr or "Push failed",
                    f"Git push failed: {stderr or 'unknown error'}. Check your remote configuration and credentials.",
                )

            output = (result.stdout or "").strip() + " " + (result.stderr or "").strip()
            return {
                "status": "success",
                "message": f"Pushed to {remote}" + (f" ({branch})" if branch else ""),
                "data": {
                    "remote": remote,
                    "branch": branch or "(current)",
                    "output": output.strip(),
                    "cwd": resolved,
                },
            }

        return error_handler.wrap_automation(
            func=_push,
            operation_name="Git Push",
            context={"cwd": resolved, "remote": remote},
        )


# ===================================================================
# Tool: git.pull
# ===================================================================

class GitPullTool(BaseTool):
    name = "git.pull"
    description = "Pull latest changes from remote"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, cwd: str = ".", remote: str = "origin", branch: str = "") -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _pull():
            _ensure_git_repo(resolved)

            pull_args = ["pull", remote]
            if branch and branch.strip():
                pull_args.append(branch.strip())

            result = _run_git(pull_args, resolved, timeout=60)

            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise AutomationError(
                    stderr or "Pull failed",
                    f"Git pull failed: {stderr or 'unknown error'}.",
                )

            output = (result.stdout or "").strip()
            already_up_to_date = "already up to date" in output.lower()

            return {
                "status": "success",
                "message": "Already up to date." if already_up_to_date else f"Pulled latest from {remote}.",
                "data": {
                    "remote": remote,
                    "branch": branch or "(current)",
                    "output": output,
                    "cwd": resolved,
                    "up_to_date": already_up_to_date,
                },
            }

        return error_handler.wrap_automation(
            func=_pull,
            operation_name="Git Pull",
            context={"cwd": resolved, "remote": remote},
        )


# ===================================================================
# Tool: git.log
# ===================================================================

class GitLogTool(BaseTool):
    name = "git.log"
    description = "Show recent git commit history"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, cwd: str = ".", count: int = 10) -> Dict[str, Any]:
        resolved = os.path.abspath(cwd)

        def _log():
            _ensure_git_repo(resolved)

            safe_count = max(1, min(int(count), 50))
            result = _run_git(
                ["log", f"--oneline", f"-n", str(safe_count)],
                resolved,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "does not have any commits" in stderr:
                    return {
                        "status": "success",
                        "message": "This repository has no commits yet.",
                        "data": {"commits": [], "cwd": resolved},
                    }
                raise AutomationError(stderr, f"Git log failed: {stderr}")

            commits = []
            for line in result.stdout.strip().splitlines():
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    commits.append({"hash": parts[0], "message": parts[1]})
                elif parts:
                    commits.append({"hash": parts[0], "message": ""})

            if not commits:
                msg = "No commits found."
            elif len(commits) == 1:
                msg = f"Last commit: {commits[0]['message']} ({commits[0]['hash']})"
            else:
                msg = f"Last {len(commits)} commits. Most recent: {commits[0]['message']} ({commits[0]['hash']})"

            return {
                "status": "success",
                "message": msg,
                "data": {"commits": commits, "cwd": resolved},
            }

        return error_handler.wrap_automation(
            func=_log,
            operation_name="Git Log",
            context={"cwd": resolved, "count": count},
        )
