"""MegaFish CLI — HTTP client for Flask API."""

import os
import tempfile
import time
from typing import Callable, Optional

import requests

BASE = "http://localhost:5001"


def generate_ontology(prompt: str, file_path: Optional[str] = None) -> dict:
    """
    Create a project, upload document(s), and start async ontology generation.

    If file_path is None, the prompt itself is written to a temporary .txt file
    so the API (which requires at least one document) still works.

    Returns dict with keys: project_id, task_id, status.
    """
    _tmp = None
    try:
        if file_path:
            upload_path = file_path
            fname = os.path.basename(file_path)
        else:
            # Write prompt as a synthetic scenario document
            _tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            )
            _tmp.write(prompt)
            _tmp.flush()
            _tmp.close()
            upload_path = _tmp.name
            fname = "scenario.txt"

        with open(upload_path, "rb") as fh:
            r = requests.post(
                f"{BASE}/api/graph/ontology/generate",
                data={
                    "simulation_requirement": prompt,
                    "project_name": prompt[:80],
                },
                files={"files": (fname, fh)},
                timeout=30,
            )
        r.raise_for_status()
        return r.json()
    finally:
        if _tmp and os.path.exists(_tmp.name):
            os.unlink(_tmp.name)


def build_graph(project_id: str) -> dict:
    """Start async graph build for a project that already has ontology generated."""
    r = requests.post(
        f"{BASE}/api/graph/build",
        json={"project_id": project_id},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def poll_task(
    task_id: str,
    on_progress: Optional[Callable[[str], None]] = None,
    interval: int = 2,
) -> dict:
    """Poll GET /api/graph/task/<task_id> until terminal state."""
    while True:
        r = requests.get(f"{BASE}/api/graph/task/{task_id}", timeout=10)
        r.raise_for_status()
        payload = r.json()
        # API wraps result in {"success": true, "data": {...}}
        data = payload.get("data") or payload
        status = data.get("status", "")
        if on_progress:
            msg = data.get("message") or data.get("progress") or status
            on_progress(str(msg))
        if status in ("completed", "failed", "error"):
            return data
        time.sleep(interval)


def create_simulation(project_id: str) -> dict:
    """Create a new simulation for a project that has a completed graph."""
    r = requests.post(
        f"{BASE}/api/simulation/create",
        json={"project_id": project_id},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def prepare_simulation(sim_id: str) -> dict:
    """Start async simulation preparation (generate agent personas)."""
    r = requests.post(
        f"{BASE}/api/simulation/prepare",
        json={"simulation_id": sim_id},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def poll_prepare(
    task_id: str,
    sim_id: str,
    on_progress: Optional[Callable[[str], None]] = None,
    interval: int = 3,
) -> dict:
    """Poll POST /api/simulation/prepare/status until ready."""
    while True:
        r = requests.post(
            f"{BASE}/api/simulation/prepare/status",
            json={"task_id": task_id, "simulation_id": sim_id},
            timeout=10,
        )
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data") or payload
        status = data.get("status", "")
        progress = data.get("progress", 0)
        msg = data.get("message") or f"{progress}%"
        if on_progress:
            on_progress(str(msg))
        if data.get("already_prepared") or status in ("ready", "completed"):
            return data
        if status in ("failed", "error"):
            raise RuntimeError(f"Simulation prepare failed: {msg}")
        time.sleep(interval)


def start_simulation(sim_id: str) -> dict:
    """Start the simulation process after preparation is complete."""
    r = requests.post(
        f"{BASE}/api/simulation/start",
        json={"simulation_id": sim_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def poll_simulation(
    sim_id: str,
    on_progress: Optional[Callable[[str], None]] = None,
    interval: int = 3,
) -> dict:
    """Poll GET /api/simulation/<sim_id> until terminal state."""
    while True:
        r = requests.get(f"{BASE}/api/simulation/{sim_id}", timeout=10)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data") or payload
        status = data.get("status", "")
        if on_progress:
            msg = data.get("message") or data.get("current_round") or status
            on_progress(str(msg))
        if status in ("completed", "failed", "error", "stopped"):
            return data
        time.sleep(interval)


def generate_report(sim_id: str) -> dict:
    """Start async report generation. Returns {report_id, task_id, ...}"""
    r = requests.post(
        f"{BASE}/api/report/generate",
        json={"simulation_id": sim_id},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def poll_report(
    task_id: str,
    on_progress: Optional[Callable[[str], None]] = None,
    interval: int = 3,
) -> dict:
    """Poll task until report generation completes."""
    while True:
        r = requests.get(f"{BASE}/api/graph/task/{task_id}", timeout=10)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data") or payload
        status = data.get("status", "")
        if on_progress:
            on_progress(str(data.get("message") or status))
        if status in ("completed", "failed", "error"):
            return data
        time.sleep(interval)


def get_result_url(report_id: str, port: int = 3000) -> str:
    return f"http://localhost:{port}/report/{report_id}"
