from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator

from cedric.catalog import DATABASES, FRAMEWORKS, TEMPLATE_VERSION

Framework = Literal["django", "fastapi", "flask"]
Database = Literal["sqlite", "turso", "postgres-local", "neon", "aws-rds"]
Auth = Literal["jwt"]


class ProjectSpec(BaseModel):
    name: str
    framework: Framework
    database: Database = "sqlite"
    auth: Auth = "jwt"
    package_name: str | None = None
    template_version: str = TEMPLATE_VERSION
    include_docker: bool = True
    include_ci: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value):
            raise ValueError("Use letters, numbers, underscores, or hyphens; start with a letter.")
        return value

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, value: str) -> str:
        if value not in FRAMEWORKS:
            raise ValueError(f"Unsupported framework: {value}")
        return value

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        if value not in DATABASES:
            raise ValueError(f"Unsupported database: {value}")
        return value

    def normalized_package(self) -> str:
        raw = self.package_name or self.name
        value = re.sub(r"[^A-Za-z0-9_]", "_", raw).lower()
        if value[0].isdigit():
            value = f"app_{value}"
        return value

    def project_dir(self, target_dir: Path) -> Path:
        return target_dir / self.name

    def metadata(self) -> dict[str, object]:
        return {
            "name": self.name,
            "framework": self.framework,
            "database": self.database,
            "auth": self.auth,
            "package_name": self.normalized_package(),
            "template_version": self.template_version,
            "enabled_modules": {
                "auth": self.auth == "jwt",
                "docker": self.include_docker,
                "ci": self.include_ci,
            },
        }
