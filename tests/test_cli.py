from typer.testing import CliRunner

from cedric.cli import app

runner = CliRunner()


def test_templates_list_command():
    result = runner.invoke(app, ["templates", "list"])

    assert result.exit_code == 0
    assert "fastapi" in result.output
    assert "postgres-local" in result.output


def test_version_command():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Cedric 2.0.1" in result.output


def test_new_and_doctor_commands(tmp_path):
    result = runner.invoke(
        app,
        [
            "new",
            "demo",
            "--framework",
            "flask",
            "--database",
            "sqlite",
            "--target-dir",
            str(tmp_path),
            "--no-input",
        ],
    )

    assert result.exit_code == 0, result.output
    doctor = runner.invoke(app, ["doctor", str(tmp_path / "demo")])
    assert doctor.exit_code == 0, doctor.output
