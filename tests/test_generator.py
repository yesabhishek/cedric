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
    assert not (root / "uv.lock").exists()
    assert ok(run_doctor(root))

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    auth = (root / "app" / "auth.py").read_text(encoding="utf-8")
    db = (root / "app" / "db.py").read_text(encoding="utf-8")
    main = (root / "app" / "main.py").read_text(encoding="utf-8")
    openapi = (root / "docs" / "openapi.yaml").read_text(encoding="utf-8")
    assert '"bcrypt>=5.0"' in pyproject
    assert "passlib" not in pyproject
    assert "HTTPBearer" in auth
    assert "OAuth2PasswordBearer" not in auth
    assert "CryptContext" not in auth
    assert "class User(Base)" in auth
    assert "Base.metadata.create_all" in db
    assert "init_db()" in main
    assert "BearerAuth:" in openapi


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


def test_add_db_preserves_default_audience_for_legacy_metadata(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )
    metadata_path = root / ".cedric" / "project.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("audience", None)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    add_module(root, "db", "neon")

    updated = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert updated["audience"] == "human-developer"
    assert updated["database"] == "neon"


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


def test_generated_dockerfile_does_not_copy_uv_lock(tmp_path):
    root = generate_project(
        ProjectSpec(name="api", framework="fastapi", database="sqlite"),
        tmp_path,
    )

    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY pyproject.toml ./" in dockerfile
    assert "uv.lock" not in dockerfile


def test_readme_human_audience_framework_and_database_conditionals(tmp_path):
    root = generate_project(
        ProjectSpec(
            name="api",
            framework="django",
            database="turso",
            audience="human-developer",
        ),
        tmp_path,
    )

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "uv run python manage.py migrate" in readme
    assert "uv run python manage.py runserver" in readme
    assert "Schema endpoint: `/api/schema/`" in readme
    assert "Open the app at `/` and the schema at `/api/schema/`." in readme
    assert "Set both `DATABASE_URL` and `TURSO_AUTH_TOKEN`" in readme
    assert "## Day-1 Workflow (Human Developer)" in readme
    assert "## Agent Workflow" not in readme


def test_readme_ai_agent_audience_section(tmp_path):
    root = generate_project(
        ProjectSpec(
            name="api",
            framework="fastapi",
            database="neon",
            audience="ai-agent",
        ),
        tmp_path,
    )

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "## Agent Workflow" in readme
    assert "## Day-1 Workflow (Human Developer)" not in readme
    assert "Use provider-managed credentials and SSL" in readme
    assert "uv run uvicorn app.main:app --reload" in readme
    assert "Open Swagger UI at `/docs` or the schema at `/openapi.json`." in readme
    assert "Schema endpoint: `/openapi.json/`" not in readme
    assert "Schema endpoint: `/openapi.json`" in readme


def test_readme_dual_audience_contains_both_sections(tmp_path):
    root = generate_project(
        ProjectSpec(
            name="api",
            framework="flask",
            database="sqlite",
            audience="dual",
        ),
        tmp_path,
    )

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "## Day-1 Workflow (Human Developer)" in readme
    assert "## Agent Workflow" in readme
    assert "uv run flask --app app run --debug" in readme
    assert "Open the schema at `/openapi.json`." in readme
