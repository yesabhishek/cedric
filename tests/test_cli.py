from typer.testing import CliRunner

from cedric import cli
from cedric.cli import app, legacy_setup

runner = CliRunner()


def test_help_lists_init_only():
    result = runner.invoke(app, ["--help"])
    normalized = " ".join(result.output.split())

    assert result.exit_code == 0
    assert "init" in normalized
    assert "doctor" not in normalized
    assert "templates" not in normalized
    assert "add" not in normalized


def test_root_command_prints_intro_and_help():
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Use `cedric init` to start project setup" in result.output
    assert "Wizard navigation: `Esc`" in result.output
    assert "init" in result.output


def test_version_command():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Cedric 2.0.3" in result.output


def test_init_with_recommended_defaults(tmp_path):
    result = runner.invoke(
        app,
        [
            "init",
            "--target-dir",
            str(tmp_path),
            "--no-input",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "my_api").exists()
    metadata = (tmp_path / "my_api" / ".cedric" / "project.json").read_text(encoding="utf-8")
    assert '"audience": "human-developer"' in metadata


def test_init_with_non_default_answers(tmp_path):
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-init",
            "--framework",
            "flask",
            "--database",
            "neon",
            "--audience",
            "dual",
            "--target-dir",
            str(tmp_path),
            "--no-input",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "demo-init").exists()
    metadata = (tmp_path / "demo-init" / ".cedric" / "project.json").read_text(encoding="utf-8")
    assert '"audience": "dual"' in metadata


def test_wizard_back_step_logic():
    answers = iter(
        [
            "demo",
            cli.BACK_SENTINEL,
            "demo2",
            "fastapi",
            "sqlite",
            "ai-agent",
        ]
    )

    def fake_prompt(_key: str, _default: str, _current: str | None) -> str:
        return next(answers)

    original = cli._wizard_prompt
    cli._wizard_prompt = fake_prompt
    try:
        result = cli._collect_init_answers(
            no_input=False,
            name=None,
            framework=None,
            database=None,
            audience=None,
        )
    finally:
        cli._wizard_prompt = original

    assert result["name"] == "demo2"
    assert result["framework"] == "fastapi"
    assert result["database"] == "sqlite"
    assert result["audience"] == "ai-agent"


def test_legacy_setup_returns_error_code():
    assert legacy_setup() == 1


def test_legacy_new_command_shows_migration_message():
    result = runner.invoke(app, ["new", "test-app", "--framework", "django"])

    assert result.exit_code == 2
    assert "has been removed" in result.output
    assert "cedric init" in result.output
    assert "Traceback" not in result.output


def test_legacy_doctor_command_shows_migration_message():
    result = runner.invoke(app, ["doctor", "."])

    assert result.exit_code == 2
    assert "has been removed" in result.output
    assert "cedric init" in result.output
    assert "Traceback" not in result.output


def test_legacy_add_command_shows_migration_message():
    result = runner.invoke(app, ["add", "db", "postgres"])

    assert result.exit_code == 2
    assert "has been removed" in result.output
    assert "cedric init" in result.output
    assert "Traceback" not in result.output


def test_legacy_templates_command_shows_migration_message():
    result = runner.invoke(app, ["templates", "list"])

    assert result.exit_code == 2
    assert "has been removed" in result.output
    assert "cedric init" in result.output
    assert "Traceback" not in result.output
