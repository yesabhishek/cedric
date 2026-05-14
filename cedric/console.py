from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

CEDRIC_GREEN = "#39ff14"

theme = Theme(
    {
        "cedric.logo": f"bold {CEDRIC_GREEN}",
        "cedric.ok": f"bold {CEDRIC_GREEN}",
        "cedric.dim": "dim",
        "cedric.error": "bold red",
        "cedric.path": "bold white",
    }
)

console = Console(theme=theme)

LOGO = r"""
   ______          __     _     
  / ____/__  ____/ /____(_)____
 / /   / _ \/ __  / ___/ / ___/
/ /___/  __/ /_/ / /  / / /__  
\____/\___/\__,_/_/  /_/\___/  
"""


def print_logo() -> None:
    console.print(LOGO, style="cedric.logo")
    console.print("clean backend systems, generated for humans and agents", style="cedric.dim")
