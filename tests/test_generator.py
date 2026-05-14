import json

from cedric.doctor import ok, run_doctor
from cedric.generator import add_module, generate_project
from cedric.models import ProjectSpec


def test_generate_fastapi_project(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )

    assert (root / "app" / "main.py").exists()
    assert (root / "AGENTS.md").exists()
    assert (root / "docs" / "openapi.yaml").exists()
    assert (root / ".cedric" / "project.json").exists()
    assert ok(run_doctor(root))


def test_generate_all_framework_entrypoints(tmp_path):
    cases = {
        "django": "manage.py",
        "fastapi": "app/main.py",
        "flask": "wsgi.py",
    }

    for framework, entrypoint in cases.items():
        root = generate_project(
            ProjectSpec(name=f"{framework}_app", framework=framework, database="sqlite"),
            tmp_path,
        )
        assert (root / entrypoint).exists()
        assert ok(run_doctor(root))


def test_add_db_updates_metadata_and_database_docs(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )

    changed = add_module(root, "db", "neon")

    metadata = json.loads((root / ".cedric" / "project.json").read_text())
    assert metadata["database"] == "neon"
    assert root / "docs" / "database.md" in changed
    assert "Neon Postgres" in (root / "docs" / "database.md").read_text()
    assert "ep-example.neon.tech" in (root / ".env.example").read_text()


def test_doctor_reports_corrupted_metadata(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )
    (root / ".cedric" / "project.json").write_text("{", encoding="utf-8")

    checks = run_doctor(root)

    assert not ok(checks)
    assert any(check.name == "metadata json" and not check.ok for check in checks)


def test_doctor_reports_missing_env(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )
    (root / ".env.example").unlink()

    checks = run_doctor(root)

    assert not ok(checks)
    assert any(check.name == ".env.example" and not check.ok for check in checks)
