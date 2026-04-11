"""Workflow definitions for common assistant intents."""
from __future__ import annotations

from backend.utils.logger import log


def start_work_session():
    log(f"Workflow: start_work_session - preparing 3 steps")
    return [
        {"action": "open_app", "params": {"app_name": "code"}},
        {"action": "run_command", "params": {"command": "jupyter notebook"}},
        {"action": "open_url", "params": {"url": "http://localhost:8888"}},
    ]


def organize_files():
    log(f"Workflow: organize_files - preparing 2 steps")
    return [
        {"action": "list_directory", "params": {"path": "./"}},
        {"action": "organize_folder", "params": {"path": "./"}},
    ]


def run_command_workflow(command: str = ""):
    log(f"Workflow: run_command_workflow - preparing 1 step with command '{command}'")
    return [
        {"action": "run_command", "params": {"command": command}},
    ]


def open_app_workflow(app_name: str = ""):
    log(f"Workflow: open_app_workflow - preparing 1 step to open app '{app_name}'")
    return [
        {"action": "open_app", "params": {"app_name": app_name}},
    ]


def search_web_workflow(query: str = ""):
    log(f"Workflow: search_web_workflow - preparing 1 step to search for '{query}'")
    return [
        {"action": "search_google", "params": {"query": query}},
    ]


def continue_work_workflow(last_plan: str = "", last_project: str = "", last_intent: str = ""):
    if last_project:
        log(
            f"Workflow: continue_work_workflow - resuming project '{last_project}' with goal '{last_plan}'"
        )
        return [
            {"action": "open_project", "params": {"path": last_project}},
            {
                "action": "run_command",
                "params": {
                    "command": "echo Resuming previous work context",
                    "cwd": last_project,
                },
            },
        ]

    if last_intent == "start_work_session":
        log("Workflow: continue_work_workflow - restoring previous start_work_session workflow")
        return start_work_session()

    log("Workflow: continue_work_workflow - no last project, returning memory summary step")
    return [
        {"action": "list_memory", "params": {}},
    ]


def open_project_workflow(project_path: str = ""):
    log(f"Workflow: open_project_workflow - preparing 1 step to open project '{project_path}'")
    return [
        {"action": "open_project", "params": {"path": project_path}},
    ]