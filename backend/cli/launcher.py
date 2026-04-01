"""MegaFish CLI — service lifecycle manager."""

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import requests

from .ui import status, success, error

# Paths
_ROOT = Path(__file__).parent.parent.parent  # project root
_BACKEND_DIR = _ROOT / "backend"
_FRONTEND_DIR = _ROOT / "frontend"

# Tracked subprocesses
_procs: list[subprocess.Popen] = []


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_neo4j() -> bool:
    return _port_open("localhost", 7687)


def check_ollama() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code < 500
    except Exception:
        return False


def check_backend() -> bool:
    try:
        r = requests.get("http://localhost:5001/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def check_frontend() -> bool:
    for port in (3000, 3001):
        try:
            r = requests.get(f"http://localhost:{port}", timeout=2)
            if r.status_code < 500:
                return port
        except Exception:
            pass
    return False


def _wait_for(check_fn, label: str, timeout: int = 30) -> bool:
    for _ in range(timeout):
        if check_fn():
            return True
        time.sleep(1)
    error(f"{label} did not start within {timeout}s")
    return False


def start_backend() -> bool:
    status("Starting backend...")
    python = _BACKEND_DIR / ".venv" / "bin" / "python"
    if not python.exists():
        python = Path(sys.executable)
    proc = subprocess.Popen(
        [str(python), "run.py"],
        cwd=str(_BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _procs.append(proc)
    return _wait_for(check_backend, "Backend", timeout=30)


def start_frontend() -> int | None:
    status("Starting frontend...")
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _procs.append(proc)
    for _ in range(20):
        port = check_frontend()
        if port:
            return port
        time.sleep(1)
    error("Frontend did not start within 20s")
    return None


def ensure_services() -> int:
    """Check all 4 services, start what's missing. Returns frontend port."""
    # Neo4j
    if check_neo4j():
        success("Neo4j        running")
    else:
        error("Neo4j not running — start it with: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/megafish neo4j:5.18-community")

    # Ollama
    if check_ollama():
        success("Ollama        running")
    else:
        error("Ollama not running — start it with: ollama serve")

    # Backend
    if check_backend():
        success("Backend       running")
    else:
        start_backend()
        if check_backend():
            success("Backend       started")

    # Frontend
    port = check_frontend()
    if port:
        success(f"Frontend      running  →  http://localhost:{port}")
        return port
    else:
        port = start_frontend()
        if port:
            success(f"Frontend      started  →  http://localhost:{port}")
            return port
        return 3000


def open_browser(url: str):
    webbrowser.open_new_tab(url)


def stop_all():
    for proc in _procs:
        try:
            proc.terminate()
        except Exception:
            pass
    _procs.clear()
