"""MegaFish CLI — first-run install wizard."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.theme import Theme

from .ui import FISH_ART, LOGO_TEXT, console, success, error, status

_MARKER = Path.home() / ".megafish" / ".installed"
_ROOT = Path(__file__).parent.parent.parent


def is_installed() -> bool:
    return _MARKER.exists()


def _run(cmd: str, shell: bool = True) -> bool:
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def _check_python() -> bool:
    return sys.version_info >= (3, 11)


def _check_uv() -> bool:
    return shutil.which("uv") is not None


def _check_node() -> bool:
    if not shutil.which("node"):
        return False
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        ver = r.stdout.strip().lstrip("v").split(".")
        return int(ver[0]) >= 18
    except Exception:
        return False


def _check_brew() -> bool:
    return shutil.which("brew") is not None


def _install_brew_if_needed():
    if _is_mac() and not _check_brew():
        status("Installing Homebrew...")
        _run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
        # Add brew to PATH for this session
        _run('eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true')


def _check_ollama() -> bool:
    return shutil.which("ollama") is not None


def _is_mac() -> bool:
    return platform.system() == "Darwin"


def _is_linux() -> bool:
    return platform.system() == "Linux"


def run_install():
    console.print(FISH_ART, style="bold red")
    console.print(LOGO_TEXT, style="bold red")
    console.print("  MegaFish Installer v0.2.0\n", style="bold red")
    console.print("─" * 66, style="red")

    if not Confirm.ask("[red]Do you trust this directory?[/red]", default=False):
        error("Installation cancelled.")
        sys.exit(0)

    if not Confirm.ask("[red]Allow MegaFish to store simulation data here?[/red]", default=False):
        error("Installation cancelled.")
        sys.exit(0)

    console.print("\n[bold red]Checking dependencies...[/bold red]\n")

    # Homebrew (macOS only, must come first)
    if _is_mac():
        if _check_brew():
            success("Homebrew")
        else:
            _install_brew_if_needed()
            success("Homebrew") if _check_brew() else error("Homebrew install failed — install manually: https://brew.sh")

    # Python 3.11+
    if _check_python():
        success("Python 3.11+")
    else:
        status("Installing Python 3.11...")
        if _is_mac():
            _run("brew install python@3.11")
        elif _is_linux():
            _run("sudo apt-get install -y python3.11 python3.11-venv")
        if _check_python():
            success("Python 3.11+")
        else:
            error("Python 3.11+ install failed — please install manually")

    # uv
    if _check_uv():
        success("uv")
    else:
        status("Installing uv...")
        _run("curl -LsSf https://astral.sh/uv/install.sh | sh")
        if _check_uv():
            success("uv")
        else:
            error("uv install failed — please install manually: curl -LsSf https://astral.sh/uv/install.sh | sh")

    # Node.js 18+
    if _check_node():
        success("Node.js 18+")
    else:
        status("Installing Node.js...")
        if _is_mac():
            _run("brew install node")
        elif _is_linux():
            _run("curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs")
        if _check_node():
            success("Node.js 18+")
        else:
            error("Node.js 18+ install failed — please install manually")

    # Neo4j (native via Homebrew)
    status("Installing/starting Neo4j...")
    if not shutil.which("neo4j") and _is_mac():
        _run("brew install neo4j")
    _run("neo4j-admin dbms set-initial-password megafish 2>/dev/null || true")
    _run("neo4j start")
    success("Neo4j")

    # Ollama
    if _check_ollama():
        success("Ollama")
    else:
        status("Installing Ollama...")
        _run("curl -fsSL https://ollama.com/install.sh | sh")
        if _check_ollama():
            success("Ollama")
        else:
            error("Ollama install failed — please install manually: https://ollama.com")

    # Python packages
    status("Installing Python packages...")
    backend_dir = _ROOT / "backend"
    _run(f"cd {backend_dir} && uv venv --python 3.11 .venv && uv pip install -r requirements.txt")
    success("Python packages")

    # Node packages
    status("Installing Node packages...")
    _run(f"cd {_ROOT} && npm install && cd frontend && npm install")
    success("Node packages")

    # .env
    env_file = _ROOT / ".env"
    env_example = _ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        import shutil as _shutil
        _shutil.copy(env_example, env_file)
        success(".env created from .env.example")

    # Ollama model
    if Confirm.ask("[red]Pull qwen2.5:7b model now? (recommended, ~4.7GB)[/red]", default=False):
        status("Pulling qwen2.5:7b (this may take a while)...")
        _run("ollama pull qwen2.5:7b")
        success("qwen2.5:7b")
    else:
        status("Skipped model pull — run 'ollama pull qwen2.5:7b' when ready")

    # Write marker
    _MARKER.parent.mkdir(parents=True, exist_ok=True)
    _MARKER.write_text("installed")

    console.print("\n", style="red")
    success("All packages installed.")
    console.print("\n  Run: [bold red]megafish[/bold red]\n", style="red")


def _detect_repo_root() -> Path | None:
    """
    Find the git repository root that contains this installation.

    Priority:
    1. Standard install path: ~/.megafish/app
    2. Development clone: walk up from this file's directory looking for .git
    """
    # Try the install.sh bootstrap path first
    install_dir = Path.home() / ".megafish" / "app"
    if install_dir.exists() and (install_dir / ".git").exists():
        return install_dir

    # Walk up from backend/cli/installer.py to find a .git directory
    candidate = _ROOT  # project root (backend/../..)
    for _ in range(4):  # at most 4 levels up
        if (candidate / ".git").exists():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent

    return None


def run_update():
    repo_root = _detect_repo_root()

    if repo_root is None:
        error(
            "Cannot determine the MegaFish repository location.\n"
            "  If you installed via install.sh, expected: ~/.megafish/app\n"
            "  If you cloned the repo, run: git pull && uv pip install -e '.[cli]'"
        )
        sys.exit(1)

    # Check if this is actually a git repo we can pull
    if not _run(f"git -C {repo_root} rev-parse --is-inside-work-tree"):
        error(f"'{repo_root}' is not a git repository. Cannot auto-update.")
        sys.exit(1)

    status(f"Updating from git at {repo_root}...")
    if not _run(f"git -C {repo_root} pull"):
        error("git pull failed — check your internet connection and repository access.")
        sys.exit(1)

    # Reinstall Python dependencies
    backend_dir = repo_root / "backend"
    venv_pip = backend_dir / ".venv" / "bin" / "pip"
    status("Reinstalling Python dependencies...")
    if venv_pip.exists():
        _run(f"{venv_pip} install -e '{backend_dir}[cli]' --quiet")
    elif shutil.which("uv"):
        _run(f"cd {backend_dir} && uv sync")
    else:
        status("Skipping dependency reinstall — no .venv or uv found. Run manually if needed.")

    success("MegaFish updated. Run megafish to start.")


def run_uninstall():
    console.print(FISH_ART, style="bold red")
    console.print(LOGO_TEXT, style="bold red")
    console.print("  MegaFish Uninstaller\n", style="bold red")
    console.print("─" * 66, style="red")

    if not Confirm.ask("[red]Are you sure you want to uninstall MegaFish?[/red]", default=False):
        status("Uninstall cancelled.")
        sys.exit(0)

    # Stop running services
    try:
        from . import launcher
        launcher.stop_all()
        success("Services stopped.")
    except Exception:
        pass

    # Stop Neo4j
    if shutil.which("neo4j"):
        status("Stopping Neo4j...")
        _run("neo4j stop")
        success("Neo4j stopped.")

    # Optionally remove simulation data
    megafish_dir = Path.home() / ".megafish"
    if megafish_dir.exists():
        if Confirm.ask(f"[red]Remove simulation data in {megafish_dir}?[/red]", default=False):
            shutil.rmtree(megafish_dir)
            success(f"Removed {megafish_dir}")
    else:
        # Remove just the marker if data dir doesn't exist
        if _MARKER.exists():
            _MARKER.unlink()

    # Remove the wrapper script
    wrapper = Path("/usr/local/bin/megafish")
    if wrapper.exists():
        try:
            wrapper.unlink()
            success("Removed /usr/local/bin/megafish")
        except PermissionError:
            _run("sudo rm /usr/local/bin/megafish")
            success("Removed /usr/local/bin/megafish")

    console.print()
    success("MegaFish uninstalled.")
