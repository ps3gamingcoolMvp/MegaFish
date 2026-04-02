"""MegaFish CLI — terminal UI (red theme)."""

import os
from rich.box import Box
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.prompt import Prompt
import sys

# Panel box with no bottom border (bottom row is spaces → invisible on dark bg)
_NO_BOTTOM = Box(
    "╭──╮\n"
    "│  │\n"
    "├──┤\n"
    "│  │\n"
    "├──┤\n"
    "├──┤\n"
    "│  │\n"
    "    \n"
)

err_console = Console(stderr=True, theme=Theme({"default": "bold red"}))

FISH_ART = r"""
                          .
                          A       ;
                |   ,--,-/ \---,-/|  ,
               _|\,'. /|      /|   `/|-.
           \`.'    /|      ,            `;.
          ,'\   A     A         A   A _ /| `.;
        ,/  _              A       _  / _   /|  ;
       /\  / \   ,  ,           A  /    /     `/|
      /_| | _ \         ,     ,             ,/  \
     // | |/ `.\  ,-      ,       ,   ,/ ,/      \/
     / @| |@  / /'   \  \      ,              >  /|    ,--.
    |\_/   \_/ /      |  |           ,  ,/        \  ./' __:..
    |  __ __  |       |  | .--.  ,         >  >   |-'   /     `
  ,/| /  '  \ |       |  |     \      ,           |    /
 /  |<--.__,->|       |  | .    `.        >  >    /   (
/_,' \\  ^  /  \     /  /   `.    >--            /^\   |
      \\___/    \   /  /      \__'     \   \   \/   \  |
       `.   |/          ,  ,                  /`\    \  )
         \  '  |/    ,       V    \          /        `-\
          `|/  '  V      V           \    \.'            \_
           '`-.       V       V        \./'\
               `|/-.      \ /   \ /,---`\
                /   `._____V_____V'
                           '     '
"""

LOGO_TEXT = r"""
███╗   ███╗███████╗ ██████╗  █████╗ ███████╗██╗███████╗██╗  ██╗
████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔════╝██║██╔════╝██║  ██║
██╔████╔██║█████╗  ██║  ███╗███████║█████╗  ██║███████╗███████║
██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║██╔══╝  ██║╚════██║██╔══██║
██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║██║     ██║███████║██║  ██║
╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
"""

console = Console(theme=Theme({"default": "bold red"}))


def _center_block(text: str) -> str:
    """Shift every line by the same left-pad so the widest line is centered."""
    try:
        w = os.get_terminal_size().columns
    except OSError:
        w = 80
    lines = text.splitlines()
    max_len = max((len(line) for line in lines), default=0)
    pad = max(0, (w - max_len) // 2)
    return "\n".join(" " * pad + line for line in lines)


def splash():
    console.clear()
    # Fish art: shift as a rigid block so the shape stays intact
    console.print(_center_block(FISH_ART), style="bold red", markup=False)
    # Logo and text: symmetric, fine to center line-by-line
    console.print(LOGO_TEXT, style="bold red", justify="center")
    console.print("v0.2.0  —  Multi-agent swarm intelligence engine", style="red", justify="center")
    console.print("─" * 66, style="red", justify="center")
    console.print()


def info_panel():
    lines = [
        "  [bold red]What it does[/bold red]",
        "  Simulates public reaction to any scenario using AI agent swarms.",
        "  Builds a knowledge graph · generates personas · runs social media sim.",
        "  Results open in your browser at [red]localhost:3000[/red]",
        "",
        "  [bold red]Commands[/bold red]",
        "  [red]megafish[/red]                run a simulation",
        "  [red]megafish update[/red]         update to the latest version",
        "  [red]megafish uninstall[/red]      uninstall MegaFish",
        "  [red]megafish status[/red]         show status of all services",
        "  [red]megafish stop[/red]           stop all running services",
        "  [red]megafish help[/red]           show this info",
    ]
    content = "\n".join(lines)
    console.print(Panel(content, border_style="red", padding=(0, 1)))
    console.print()


def prompt_box() -> str:
    console.print(Panel(
        "[red]Enter a scenario to simulate:[/red]\n"
        "[dim]e.g. 'Apple announces $500 iPhone'  ·  'NATO expands to include Ukraine'[/dim]\n\n"
        "[dim]Press Ctrl+C to exit[/dim]",
        box=_NO_BOTTOM,
        border_style="bold red",
        title="[bold red]  Scenario  [/bold red]",
        padding=(1, 2),
    ))
    value = Prompt.ask("[bold red]  >[/bold red]")
    console.print()
    return value


def ask_file() -> str | None:
    while True:
        answer = Prompt.ask("[red]Attach a file? (path or Enter to skip)[/red]", default="")
        answer = answer.strip()
        if not answer:
            return None
        if os.path.exists(answer):
            return answer
        console.print(f"[red]✗[/red] File not found: {answer!r} — press Enter to skip")


def status(msg: str):
    console.print(f"[red]●[/red] {msg}")


def success(msg: str):
    console.print(f"[bold red]✓[/bold red] {msg}")


def error(msg: str):
    err_console.print(f"[bold red]✗[/bold red] {msg}")


def progress(msg: str):
    from rich.progress import Progress, SpinnerColumn, TextColumn
    return Progress(
        SpinnerColumn(style="red"),
        TextColumn(f"[red]{msg}[/red]"),
        console=console,
    )
