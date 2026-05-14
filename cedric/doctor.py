from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cedric.catalog import DATABASES, FRAMEWORKS


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


REQUIRED_PATHS = [
    "pyproject.toml",
    "README.md",
    "AGENTS.md",
    ".env.example",
    ".cedric/project.json",
    "docs/openapi.yaml",
    "docs/auth.md",
    "docs/database.md",
    "tests/test_smoke.py",
]


def run_doctor(project_root: Path) -> list[Check]:
    checks: list[Check] = []
    metadata_path = project_root / ".cedric" / "project.json"

    for relative in REQUIRED_PATHS:
        path = project_root / relative
        checks.append(Check(relative, path.exists(), "found" if path.exists() else "missing"))

    if not metadata_path.exists():
        return checks

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(Check("metadata json", False, f"invalid JSON: {exc.msg}"))
        return checks

    framework = metadata.get("framework")
    database = metadata.get("database")
    checks.append(
        Check(
            "framework",
            framework in FRAMEWORKS,
            str(framework) if framework in FRAMEWORKS else f"unsupported: {framework}",
        )
    )
    checks.append(
        Check(
            "database",
            database in DATABASES,
            str(database) if database in DATABASES else f"unsupported: {database}",
        )
    )

    if framework == "fastapi":
        checks.append(_exists(project_root, "app/main.py"))
    elif framework == "flask":
        checks.append(_exists(project_root, "wsgi.py"))
    elif framework == "django":
        checks.append(_exists(project_root, "manage.py"))

    env_path = project_root / ".env.example"
    env_text = env_path.read_text(encoding="utf-8", errors="ignore") if env_path.exists() else ""
    checks.append(Check("DATABASE_URL", "DATABASE_URL=" in env_text, "declared in .env.example"))
    checks.append(Check("SECRET_KEY", "SECRET_KEY=" in env_text, "declared in .env.example"))

    return checks


def _exists(root: Path, relative: str) -> Check:
    path = root / relative
    return Check(relative, path.exists(), "found" if path.exists() else "missing")


def ok(checks: list[Check]) -> bool:
    return all(check.ok for check in checks)
