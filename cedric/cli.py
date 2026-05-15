from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.text import Text

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:  # pragma: no cover - dependency should be present in normal installs
    PromptSession = None
    KeyBindings = None

from cedric.catalog import DATABASES, FRAMEWORKS
from cedric.console import console, print_logo
from cedric.generator import GenerationError, generate_project
from cedric.models import Audience, Database, Framework, ProjectSpec

app = typer.Typer(
    name="cedric",
    help="Interactive backend project setup. Use `cedric init` to start.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)
BACK_SENTINEL = "__CEDRIC_BACK__"


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show Cedric version and exit."),
    ] = False,
) -> None:
    if version:
        from cedric import __version__

        console.print(f"Cedric {__version__}", style="cedric.ok")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        print_logo()
        help_text = Text.from_ansi(ctx.get_help())
        console.print(
            Panel(
                "Use `cedric init` to start project setup.\n"
                "Wizard navigation: `Esc` to go back, or `Backspace/Delete` on empty input.",
                title="Cedric CLI",
                border_style="cedric.ok",
            )
        )
        console.print(help_text)
        raise typer.Exit()

@app.command("init")
def init_project(
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
        typer.Option(
            "--no-input",
            help="Use recommended defaults without prompting (for scripts/tests).",
        ),
    ] = False,
    name: Annotated[
        str | None,
        typer.Option("--name", help="Project name. If omitted, wizard asks for it."),
    ] = None,
    framework: Annotated[
        Framework | None,
        typer.Option("--framework", "-f", help="Framework preset override."),
    ] = None,
    database: Annotated[
        Database | None,
        typer.Option("--database", "-d", help="Database preset override."),
    ] = None,
    audience: Annotated[
        Audience | None,
        typer.Option("--audience", help="README audience preset override."),
    ] = None,
) -> None:
    """Start the interactive setup wizard for a new backend project."""

    print_logo()
    answers = _collect_init_answers(
        no_input=no_input,
        name=name,
        framework=framework,
        database=database,
        audience=audience,
    )
    try:
        spec = ProjectSpec(
            name=answers["name"],
            framework=answers["framework"],
            database=answers["database"],
            audience=answers["audience"],
        )
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


LEGACY_CONTEXT = {"allow_extra_args": True, "ignore_unknown_options": True}


@app.command("new", hidden=True, context_settings=LEGACY_CONTEXT)
def legacy_new(
    ctx: typer.Context,
    _: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    _legacy_removed("new", ctx.args)


def legacy_setup() -> int:
    """Compatibility entry point for removed command."""
    console.print(
        Panel(
            "`cedric-setup` has been removed.\n"
            "Use the guided setup command instead: `cedric init`.",
            title="Command removed",
            border_style="cedric.error",
        )
    )
    return 1


def _collect_init_answers(
    no_input: bool,
    name: str | None,
    framework: Framework | None,
    database: Database | None,
    audience: Audience | None,
) -> dict[str, str]:
    defaults = {
        "name": "my_api",
        "framework": "fastapi",
        "database": "sqlite",
        "audience": "human-developer",
    }
    if no_input:
        return {
            "name": name or defaults["name"],
            "framework": framework or defaults["framework"],
            "database": database or defaults["database"],
            "audience": audience or defaults["audience"],
        }

    initial = {
        "name": name,
        "framework": framework,
        "database": database,
        "audience": audience,
    }
    answers: dict[str, str] = {}
    steps = ("name", "framework", "database", "audience")
    idx = 0
    while idx < len(steps):
        key = steps[idx]
        if initial[key]:
            answers[key] = str(initial[key])
            idx += 1
            continue

        value = _wizard_prompt(key, defaults[key], answers.get(key))
        if value == BACK_SENTINEL:
            if idx == 0:
                console.print("[cedric.error]Already at the first question.[/]")
                continue
            prev_key = steps[idx - 1]
            answers.pop(prev_key, None)
            idx -= 1
            continue
        answers[key] = value
        idx += 1

    return answers


def _wizard_prompt(key: str, default: str, current: str | None) -> str:
    prompt_text = _prompt_text_for(key, default)
    if not console.is_terminal or PromptSession is None or KeyBindings is None:
        return _fallback_prompt(key, prompt_text, current or default)

    session = PromptSession()
    bindings = KeyBindings()

    @bindings.add("escape")
    def _esc(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result=BACK_SENTINEL)

    @bindings.add("c-h")
    def _backspace(event) -> None:  # type: ignore[no-untyped-def]
        if not event.current_buffer.text:
            event.app.exit(result=BACK_SENTINEL)
        else:
            event.current_buffer.delete_before_cursor(count=1)

    @bindings.add("delete")
    def _delete(event) -> None:  # type: ignore[no-untyped-def]
        if not event.current_buffer.text:
            event.app.exit(result=BACK_SENTINEL)
        else:
            event.current_buffer.delete(count=1)

    while True:
        try:
            value = session.prompt(
                prompt_text,
                default=current or default,
                key_bindings=bindings,
            )
        except KeyboardInterrupt as exc:
            raise typer.Exit(1) from exc
        value = value.strip()
        err = _validate_step(key, value)
        if err:
            console.print(f"[cedric.error]{err}[/]")
            continue
        return value


def _fallback_prompt(key: str, prompt_text: str, current: str) -> str:
    while True:
        try:
            value = typer.prompt(prompt_text, default=current)
        except KeyboardInterrupt as exc:
            raise typer.Exit(1) from exc
        value = value.strip()
        err = _validate_step(key, value)
        if err:
            console.print(f"[cedric.error]{err}[/]")
            continue
        return value


def _prompt_text_for(key: str, default: str) -> str:
    if key == "name":
        return f"Project name (recommended: {default}) > "
    if key == "framework":
        return (
            f"Framework [{', '.join(FRAMEWORKS)}] (recommended: {default}) > "
        )
    if key == "database":
        return f"Database [{', '.join(DATABASES)}] (recommended: {default}) > "
    return (
        "Audience [human-developer, ai-agent, dual] "
        f"(recommended: {default}) > "
    )


def _validate_step(key: str, value: str) -> str | None:
    if key == "name":
        try:
            ProjectSpec(name=value, framework="fastapi", database="sqlite")
        except ValueError as exc:
            return str(exc)
        return None
    if key == "framework" and value not in FRAMEWORKS:
        return f"Unsupported framework `{value}`. Choose from: {', '.join(FRAMEWORKS)}."
    if key == "database" and value not in DATABASES:
        return f"Unsupported database `{value}`. Choose from: {', '.join(DATABASES)}."
    if key == "audience" and value not in {"human-developer", "ai-agent", "dual"}:
        return (
            f"Unsupported audience `{value}`. Choose from: human-developer, ai-agent, dual."
        )
    return None


@app.command("doctor", hidden=True, context_settings=LEGACY_CONTEXT)
def legacy_doctor(
    ctx: typer.Context,
    _: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    _legacy_removed("doctor", ctx.args)


@app.command("add", hidden=True, context_settings=LEGACY_CONTEXT)
def legacy_add(ctx: typer.Context, _: Annotated[list[str] | None, typer.Argument()] = None) -> None:
    _legacy_removed("add", ctx.args)


@app.command("templates", hidden=True, context_settings=LEGACY_CONTEXT)
def legacy_templates(
    ctx: typer.Context,
    _: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    _legacy_removed("templates", ctx.args)


def _legacy_removed(command: str, args: list[str]) -> None:
    suffix = f" {' '.join(args)}" if args else ""
    console.print(
        Panel(
            f"`cedric {command}{suffix}` has been removed.\n"
            "Use the guided setup command instead: `cedric init`.",
            title="Command removed",
            border_style="cedric.error",
        )
    )
    raise typer.Exit(2)
