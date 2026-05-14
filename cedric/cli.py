from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from cedric.catalog import AUTH_MODULES, DATABASES, FRAMEWORKS
from cedric.console import console, print_logo
from cedric.doctor import ok as doctor_ok
from cedric.doctor import run_doctor
from cedric.generator import GenerationError, add_module, generate_project
from cedric.models import Database, Framework, ProjectSpec

app = typer.Typer(
    name="cedric",
    help="Generate and manage clean Python backend projects.",
    no_args_is_help=True,
    add_completion=False,
)
add_app = typer.Typer(help="Add or refresh Cedric-managed modules.", no_args_is_help=True)
templates_app = typer.Typer(help="Inspect Cedric templates.", no_args_is_help=True)
app.add_typer(add_app, name="add")
app.add_typer(templates_app, name="templates")


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Show Cedric version and exit."),
    ] = False,
) -> None:
    if version:
        from cedric import __version__

        console.print(f"Cedric {__version__}", style="cedric.ok")
        raise typer.Exit()


@app.command()
def new(
    name: Annotated[str, typer.Argument(help="Project directory name.")],
    framework: Annotated[
        Framework,
        typer.Option("--framework", "-f", help="Backend framework."),
    ] = "fastapi",
    database: Annotated[
        Database,
        typer.Option("--database", "-d", help="Database preset."),
    ] = "sqlite",
    target_dir: Annotated[
        Path,
        typer.Option("--target-dir", help="Directory where the project should be created."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace an existing generated directory."),
    ] = False,
    no_input: Annotated[
        bool,
        typer.Option("--no-input", help="Run without prompts. Designed for agents and scripts."),
    ] = False,
) -> None:
    """Create a new Cedric backend project."""

    print_logo()
    if not no_input and console.is_terminal:
        framework = typer.prompt("Framework", default=framework)
        database = typer.prompt("Database", default=database)

    try:
        spec = ProjectSpec(name=name, framework=framework, database=database)
        root = generate_project(spec, target_dir.resolve(), force=force)
    except (GenerationError, ValueError) as exc:
        console.print(Panel(str(exc), title="Generation failed", style="cedric.error"))
        raise typer.Exit(1) from exc

    console.print(
        Panel(
            f"[cedric.ok]Generated[/] [cedric.path]{root}[/]\n"
            "Next: `cd {}` then `uv sync`.".format(root.name),
            title="Cedric complete",
            border_style="cedric.ok",
        )
    )


@add_app.command("db")
def add_db(
    database: Annotated[Database, typer.Option("--database", "-d", help="Database preset.")],
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Cedric project root."),
    ] = Path("."),
) -> None:
    """Add or switch the generated database preset."""

    _run_add(project_root, "db", database)


@add_app.command("auth")
def add_auth(
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Cedric project root."),
    ] = Path("."),
) -> None:
    """Refresh JWT auth documentation and metadata."""

    _run_add(project_root, "auth")


@add_app.command("docker")
def add_docker(
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Cedric project root."),
    ] = Path("."),
) -> None:
    """Add Dockerfile and docker-compose files."""

    _run_add(project_root, "docker")


@add_app.command("ci")
def add_ci(
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Cedric project root."),
    ] = Path("."),
) -> None:
    """Add GitHub Actions CI."""

    _run_add(project_root, "ci")


@app.command()
def doctor(
    project_root: Annotated[Path, typer.Argument(help="Cedric project root.")] = Path("."),
) -> None:
    """Validate a generated project."""

    checks = run_doctor(project_root.resolve())
    table = Table(title="Cedric doctor", border_style="cedric.ok")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in checks:
        status = "[cedric.ok]ok[/]" if check.ok else "[cedric.error]fail[/]"
        table.add_row(check.name, status, check.detail)
    console.print(table)
    if not doctor_ok(checks):
        raise typer.Exit(1)


@templates_app.command("list")
def templates_list() -> None:
    """List available frameworks, databases, and auth modules."""

    table = Table(title="Cedric templates", border_style="cedric.ok")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Notes")

    for framework in FRAMEWORKS:
        table.add_row("framework", framework, "first-class v2 template")
    for key, config in DATABASES.items():
        table.add_row("database", key, config["label"])
    for key, description in AUTH_MODULES.items():
        table.add_row("auth", key, description)

    console.print(table)


def legacy_setup() -> None:
    """Deprecated compatibility entry point for the old cedric-setup command."""

    console.print(
        Panel(
            "`cedric-setup` is deprecated. Use `cedric new <name>` instead.\n"
            "Example: `cedric new my_api --framework fastapi --database sqlite`",
            title="Cedric v2",
            border_style="cedric.ok",
        )
    )
    raise typer.Exit(1)


def _run_add(project_root: Path, module: str, value: str | None = None) -> None:
    try:
        changed = add_module(project_root.resolve(), module, value)
    except (GenerationError, ValueError) as exc:
        console.print(Panel(str(exc), title="Add failed", style="cedric.error"))
        raise typer.Exit(1) from exc

    body = "\n".join(f"[cedric.path]{path}[/]" for path in changed)
    console.print(Panel(body, title=f"Updated {module}", border_style="cedric.ok"))
