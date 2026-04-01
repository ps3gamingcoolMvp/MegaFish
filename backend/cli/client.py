"""MegaFish CLI — HTTP client for Flask API."""

import time
from typing import Callable, Optional

import requests

BASE = "http://localhost:5001"


def create_project(name: str) -> dict:
    r = requests.post(f"{BASE}/api/graph/projects", json={"name": name}, timeout=10)
    r.raise_for_status()
    return r.json()


def upload_file(project_id: str, filepath: str) -> dict:
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{BASE}/api/graph/upload",
            data={"project_id": project_id},
            files={"file": f},
            timeout=30,
        )
    r.raise_for_status()
    return r.json()


def build_graph(project_id: str) -> dict:
    r = requests.post(f"{BASE}/api/graph/build", json={"project_id": project_id}, timeout=10)
    r.raise_for_status()
    return r.json()


def poll_task(task_id: str, on_progress: Optional[Callable[[str], None]] = None, interval: int = 2) -> dict:
    while True:
        r = requests.get(f"{BASE}/api/graph/tasks/{task_id}", timeout=10)
        r.raise_for_status()
        data = r.json()
        status = data.get("status", "")
        if on_progress:
            msg = data.get("message") or data.get("progress") or status
            on_progress(str(msg))
        if status in ("completed", "failed", "error"):
            return data
        time.sleep(interval)


def create_simulation(project_id: str) -> dict:
    r = requests.post(f"{BASE}/api/simulation", json={"project_id": project_id}, timeout=10)
    r.raise_for_status()
    return r.json()


def poll_simulation(sim_id: str, on_progress: Optional[Callable[[str], None]] = None, interval: int = 3) -> dict:
    while True:
        r = requests.get(f"{BASE}/api/simulation/{sim_id}", timeout=10)
        r.raise_for_status()
        data = r.json()
        status = data.get("status", "")
        if on_progress:
            msg = data.get("message") or data.get("current_round") or status
            on_progress(str(msg))
        if status in ("completed", "failed", "error"):
            return data
        time.sleep(interval)


def get_result_url(sim_id: str, port: int = 3000) -> str:
    return f"http://localhost:{port}/simulation/{sim_id}/start"
