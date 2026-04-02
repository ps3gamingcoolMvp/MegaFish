"""MegaFish CLI — entry point."""

import sys
from pathlib import Path

import typer

from . import installer, launcher
from . import ui
from .client import (
    build_graph,
    create_simulation,
    generate_ontology,
    generate_report,
    get_result_url,
    poll_prepare,
    poll_report,
    poll_simulation,
    poll_task,
    prepare_simulation,
    start_simulation,
)

app = typer.Typer(
    add_completion=False,
    help="MegaFish — multi-agent swarm intelligence engine",
    invoke_without_command=True,
)


SUBCOMMANDS = {"install", "update", "uninstall", "status", "stop", "help"}


@app.callback()
def _default(ctx: typer.Context):
    """Run MegaFish: simulate public reaction to any scenario."""
    if ctx.invoked_subcommand is not None:
        return
    raw = sys.argv[1] if len(sys.argv) > 1 else None
    prompt = raw if raw and raw not in SUBCOMMANDS else None
    try:
        if not installer.is_installed():
            installer.run_install()
        ui.splash()
        ui.info_panel()
        if not prompt:
            prompt = ui.prompt_box()
        file_path = ui.ask_file()
        ui.console.print()
        if not launcher.ensure_services():
            ui.error("Backend failed to start. Check the log above.")
            raise SystemExit(1)
        ui.console.print()
        with ui.progress("Running simulation...") as prog:
            task = prog.add_task("sim")
            try:
                result_url = _run_simulation(prompt, file_path)
            finally:
                prog.update(task, completed=100)
        ui.success(f"Done → {result_url}")
        launcher.open_browser(result_url)
    except KeyboardInterrupt:
        ui.console.print("\n[red]  Exiting MegaFish.[/red]")
        raise SystemExit(0)


def _run_simulation(prompt: str, file_path: str | None) -> str:
    """Upload document, build knowledge graph, create and run simulation. Returns result URL."""
    # Step 1: Upload document + generate ontology (async)
    ui.status("Uploading document and generating ontology..." if file_path else "Generating ontology from scenario...")
    result = generate_ontology(prompt, file_path)
    data = result.get("data") or result
    project_id = data.get("project_id")
    task_id = data.get("task_id")
    if not project_id:
        raise RuntimeError(f"Ontology generation failed: {result}")

    if task_id:
        t = poll_task(task_id, on_progress=lambda m: ui.status(f"Ontology: {m}"))
        if t.get("status") in ("failed", "error"):
            raise RuntimeError(f"Ontology generation failed: {t.get('message', 'unknown error')}")

    # Step 2: Build knowledge graph (async)
    ui.status("Building knowledge graph...")
    graph_resp = build_graph(project_id)
    graph_data = graph_resp.get("data") or graph_resp
    graph_task_id = graph_data.get("task_id")
    if graph_task_id:
        t = poll_task(graph_task_id, on_progress=lambda m: ui.status(f"Graph: {m}"))
        if t.get("status") in ("failed", "error"):
            raise RuntimeError(f"Graph build failed: {t.get('message', 'unknown error')}")

    # Step 3: Create simulation
    ui.status("Creating simulation...")
    sim_resp = create_simulation(project_id)
    sim_data = sim_resp.get("data") or sim_resp
    sim_id = sim_data.get("simulation_id") or sim_data.get("id")
    if not sim_id:
        raise RuntimeError(f"Simulation creation failed: {sim_resp}")

    # Step 4: Prepare simulation (generate agent personas)
    ui.status("Generating agent personas...")
    prep = prepare_simulation(sim_id)
    prep_data = prep.get("data") or prep
    prep_task_id = prep_data.get("task_id")
    if prep_data.get("already_prepared"):
        ui.status("Agents already prepared.")
    elif prep_task_id:
        poll_prepare(prep_task_id, sim_id,
                     on_progress=lambda m: ui.status(f"Prepare: {m}"))

    # Step 5: Start simulation
    ui.status("Starting simulation...")
    start_simulation(sim_id)

    # Step 6: Poll simulation to completion
    poll_simulation(sim_id, on_progress=lambda m: ui.status(f"Sim: {m}"))

    # Step 4: Generate report
    ui.status("Generating report...")
    rep = generate_report(sim_id)
    rep_data = rep.get("data") or rep
    report_id = rep_data.get("report_id")
    rep_task_id = rep_data.get("task_id")
    if rep_task_id:
        poll_report(rep_task_id, on_progress=lambda m: ui.status(f"Report: {m}"))
    if not report_id:
        raise RuntimeError(f"Report generation failed: {rep}")

    port = launcher.check_frontend() or 3000
    return get_result_url(report_id, port)



@app.command()
def install():
    """Run the MegaFish install wizard."""
    installer.run_install()


@app.command()
def update():
    """Pull the latest MegaFish version from GitHub."""
    installer.run_update()


@app.command()
def uninstall():
    """Uninstall MegaFish and remove all associated data."""
    installer.run_uninstall()


@app.command()
def status():
    """Show status of all MegaFish services."""
    neo4j = launcher.check_neo4j()
    ollama = launcher.check_ollama()
    backend = launcher.check_backend()
    frontend = launcher.check_frontend()
    ui.success("Neo4j") if neo4j else ui.error("Neo4j not running")
    ui.success("Ollama") if ollama else ui.error("Ollama not running")
    ui.success("Backend") if backend else ui.error("Backend not running")
    ui.success(f"Frontend → http://localhost:{frontend}") if frontend else ui.error("Frontend not running")


@app.command()
def stop():
    """Stop all MegaFish services started by this CLI."""
    launcher.stop_all()
    ui.success("All MegaFish services stopped.")


@app.command(name="help")
def help_cmd():
    """Show MegaFish commands, usage, and info."""
    ui.console.print("  [bold red]Commands[/bold red]\n")
    ui.console.print("    [red]megafish[/red]                   Run a simulation (interactive prompt)")
    ui.console.print("    [red]megafish[/red] [dim]\"your scenario\"[/dim]  Run a simulation directly")
    ui.console.print("    [red]megafish update[/red]            Pull the latest version from GitHub")
    ui.console.print("    [red]megafish status[/red]            Show Neo4j / Ollama / backend / frontend status")
    ui.console.print("    [red]megafish stop[/red]              Stop all services started by MegaFish")
    ui.console.print("    [red]megafish uninstall[/red]         Uninstall MegaFish")
    ui.console.print("    [red]megafish help[/red]              Show this help\n")
    ui.console.print("  [bold red]Examples[/bold red]\n")
    ui.console.print('    megafish [dim]"Apple announces $500 iPhone"[/dim]')
    ui.console.print('    megafish [dim]"NATO expands to include Ukraine"[/dim]')
    ui.console.print('    megafish [dim]"New climate legislation passes"[/dim]\n')
    ui.console.print("  [bold red]How it works[/bold red]\n")
    ui.console.print("    1. Builds a knowledge graph from your scenario (+ optional file)")
    ui.console.print("    2. Generates AI agent personas across demographics")
    ui.console.print("    3. Runs a social media simulation (Twitter / Reddit)")
    ui.console.print("    4. Opens results in your browser at localhost:3000\n")
    ui.console.print("  [red]v0.2.0  ·  AGPL-3.0  ·  Offline  ·  Local[/red]\n")


if __name__ == "__main__":
    app()
