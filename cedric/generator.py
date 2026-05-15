from __future__ import annotations

import json
import shutil
from pathlib import Path

from jinja2 import Environment
from rich.progress import Progress, SpinnerColumn, TextColumn

from cedric.catalog import DATABASES
from cedric.console import console
from cedric.models import ProjectSpec

env = Environment(
    autoescape=False,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

FRAMEWORK_LABELS = {
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
}


class GenerationError(RuntimeError):
    pass


def render(template: str, spec: ProjectSpec) -> str:
    return env.from_string(template).render(
        spec=spec,
        package=spec.normalized_package(),
        framework_label=FRAMEWORK_LABELS[spec.framework],
        db=DATABASES[spec.database],
        database_url=DATABASES[spec.database]["url"],
    )


def generate_project(spec: ProjectSpec, target_dir: Path, force: bool = False) -> Path:
    root = spec.project_dir(target_dir)
    if root.exists():
        if not force:
            raise GenerationError(f"{root} already exists. Use --force to replace it.")
        shutil.rmtree(root)

    files = project_files(spec)
    with Progress(
        SpinnerColumn(style="cedric.logo"),
        TextColumn("[cedric.ok]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("forging project structure", total=None)
        for relative_path, content in files.items():
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(render(content, spec), encoding="utf-8")
            if relative_path == "scripts/dev.sh":
                destination.chmod(0o755)
        progress.update(task, description="project generated")

    return root


def add_module(project_root: Path, module: str, value: str | None = None) -> list[Path]:
    metadata_path = project_root / ".cedric" / "project.json"
    if not metadata_path.exists():
        raise GenerationError(
            "This does not look like a Cedric v2 project. Missing .cedric/project.json."
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.setdefault("audience", "human-developer")
    spec = ProjectSpec(
        name=metadata["name"],
        framework=metadata["framework"],
        database=value if module == "db" and value else metadata["database"],
        auth="jwt",
        audience=metadata.get("audience", "human-developer"),
        package_name=metadata.get("package_name"),
        include_docker=metadata.get("enabled_modules", {}).get("docker", True),
        include_ci=metadata.get("enabled_modules", {}).get("ci", True),
    )

    changed: list[Path] = []
    if module == "db":
        metadata["database"] = spec.database
        for relative, content in database_files(spec).items():
            path = project_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render(content, spec), encoding="utf-8")
            changed.append(path)
    elif module == "auth":
        metadata["auth"] = "jwt"
        metadata.setdefault("enabled_modules", {})["auth"] = True
        path = project_root / "docs" / "auth.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(AUTH_DOC, spec), encoding="utf-8")
        changed.append(path)
    elif module == "docker":
        metadata.setdefault("enabled_modules", {})["docker"] = True
        for relative, content in docker_files(spec).items():
            path = project_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render(content, spec), encoding="utf-8")
            changed.append(path)
    elif module == "ci":
        metadata.setdefault("enabled_modules", {})["ci"] = True
        path = project_root / ".github" / "workflows" / "ci.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(CI_YML, spec), encoding="utf-8")
        changed.append(path)
    else:
        raise GenerationError(f"Unsupported module: {module}")

    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    changed.append(metadata_path)
    return changed


def project_files(spec: ProjectSpec) -> dict[str, str]:
    files: dict[str, str] = {
        ".cedric/project.json": json.dumps(spec.metadata(), indent=2) + "\n",
        ".env.example": ENV_EXAMPLE,
        ".gitignore": GITIGNORE,
        "AGENTS.md": AGENTS_MD,
        "README.md": GENERATED_README,
        "docs/auth.md": AUTH_DOC,
        "docs/openapi.yaml": OPENAPI_YAML,
        "docs/database.md": DATABASE_DOC,
        "docs/development.md": DEVELOPMENT_DOC,
        "docs/deployment.md": DEPLOYMENT_DOC,
        "migrations/.gitkeep": "",
        "config/settings.example.toml": SETTINGS_TOML,
        "scripts/dev.sh": DEV_SCRIPT,
        "tests/test_smoke.py": SMOKE_TEST,
    }
    files.update(project_pyproject(spec))
    files.update(database_files(spec))
    files.update(docker_files(spec))
    if spec.include_ci:
        files[".github/workflows/ci.yml"] = CI_YML

    if spec.framework == "fastapi":
        files.update(fastapi_files())
    elif spec.framework == "flask":
        files.update(flask_files())
    elif spec.framework == "django":
        files.update(django_files())
    return files


def project_pyproject(spec: ProjectSpec) -> dict[str, str]:
    deps = {
        "fastapi": [
            "fastapi>=0.111",
            "uvicorn[standard]>=0.30",
            "pydantic-settings>=2.3",
            "sqlalchemy>=2.0",
            "alembic>=1.13",
            "python-jose[cryptography]>=3.3",
            "bcrypt>=5.0",
            "python-multipart>=0.0.9",
            "email-validator>=2.2",
        ],
        "flask": [
            "flask>=3.0",
            "flask-smorest>=0.44",
            "sqlalchemy>=2.0",
            "alembic>=1.13",
            "pyjwt>=2.8",
            "passlib[bcrypt]>=1.7",
            "python-dotenv>=1.0",
        ],
        "django": [
            "django>=5.0",
            "djangorestframework>=3.15",
            "djangorestframework-simplejwt>=5.3",
            "drf-spectacular>=0.27",
            "django-environ>=0.11",
        ],
    }[spec.framework]
    if spec.database != "sqlite":
        deps.append("psycopg[binary]>=3.2" if spec.database != "turso" else "libsql-client>=0.3")
    dependency_lines = "\n".join(f'  "{dep}",' for dep in deps)
    return {
        "pyproject.toml": f"""[project]
name = "{{{{ spec.name }}}}"
version = "0.1.0"
description = "Generated by Cedric."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
{dependency_lines}
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "ruff>=0.6",
]

[tool.ruff]
line-length = 100
target-version = "py310"
""",
    }


def database_files(spec: ProjectSpec) -> dict[str, str]:
    return {
        ".env.example": ENV_EXAMPLE,
        "docs/database.md": DATABASE_DOC,
        "config/database.py": DATABASE_CONFIG,
    }


def docker_files(spec: ProjectSpec) -> dict[str, str]:
    return {
        "Dockerfile": DOCKERFILE,
        "docker-compose.yml": DOCKER_COMPOSE,
    }


def fastapi_files() -> dict[str, str]:
    return {
        "app/__init__.py": "",
        "app/main.py": FASTAPI_MAIN,
        "app/config.py": FASTAPI_CONFIG,
        "app/auth.py": FASTAPI_AUTH,
        "app/db.py": FASTAPI_DB,
    }


def flask_files() -> dict[str, str]:
    return {
        "app/__init__.py": FLASK_INIT,
        "app/config.py": FLASK_CONFIG,
        "app/auth.py": FLASK_AUTH,
        "app/db.py": FLASK_DB,
        "wsgi.py": FLASK_WSGI,
    }


def django_files() -> dict[str, str]:
    return {
        "manage.py": DJANGO_MANAGE,
        "app/__init__.py": "",
        "app/asgi.py": DJANGO_ASGI,
        "app/settings.py": DJANGO_SETTINGS,
        "app/urls.py": DJANGO_URLS,
        "app/wsgi.py": DJANGO_WSGI,
        "authentication/__init__.py": "",
        "authentication/apps.py": DJANGO_AUTH_APPS,
        "authentication/models.py": DJANGO_AUTH_MODELS,
        "authentication/serializers.py": DJANGO_AUTH_SERIALIZERS,
        "authentication/views.py": DJANGO_AUTH_VIEWS,
        "authentication/urls.py": DJANGO_AUTH_URLS,
        "authentication/migrations/__init__.py": "",
    }


ENV_EXAMPLE = """APP_NAME={{ spec.name }}
APP_ENV=local
SECRET_KEY=change-me
DATABASE_URL={{ database_url }}
TURSO_AUTH_TOKEN=
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
"""

GITIGNORE = """.venv/
__pycache__/
*.py[cod]
.env
.pytest_cache/
.ruff_cache/
data/
dist/
build/
"""

GENERATED_README = """# {{ spec.name }}

This project was generated by Cedric for {{ framework_label }} with
{{ db.label }} and JWT authentication.

## Requirements

- Python 3.10 or newer.
- `uv` for dependency management.
- Docker, if you plan to use the generated Compose setup.

## Quick Start

```bash
uv sync
cp .env.example .env
{% if spec.framework == "django" -%}
uv run python manage.py migrate
{% endif -%}
./scripts/dev.sh
```

{% if spec.framework == "django" -%}
Manual run command:

```bash
uv run python manage.py runserver
```

Open the app at `/` and the schema at `/api/schema/`.
{% elif spec.framework == "fastapi" -%}
Manual run command:

```bash
uv run uvicorn app.main:app --reload
```

Open Swagger UI at `/docs` or the schema at `/openapi.json`.
{% else -%}
Manual run command:

```bash
uv run flask --app app run --debug
```

Open the schema at `/openapi.json`.
{% endif %}

## Common Commands

```bash
uv sync
uv run pytest
uv run ruff check .
{% if spec.framework == "django" -%}
uv run python manage.py test
{% elif spec.framework == "fastapi" -%}
uv run uvicorn app.main:app --reload
{% else -%}
uv run flask --app app run --debug
{% endif -%}
./scripts/dev.sh
```

## Project Layout

```text
.
|-- .cedric/project.json
|-- .env.example
|-- AGENTS.md
|-- app/
|-- config/
|-- docs/
|-- migrations/
|-- scripts/
|-- tests/
`-- pyproject.toml
```

## Authentication API

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/password-reset`

The generated auth code is a starting point. Replace any in-memory examples with
durable user storage before production.

## OpenAPI

{% if spec.framework == "django" -%}
Schema endpoint: `/api/schema/`
{% elif spec.framework == "fastapi" -%}
Schema endpoint: `/openapi.json`
{% else -%}
Schema endpoint: `/openapi.json`
{% endif %}

The concise auth contract is also documented in `docs/openapi.yaml`.

Additional guides:

- `docs/auth.md`
- `docs/database.md`
- `docs/development.md`
- `docs/deployment.md`

## Database

Selected database: {{ db.label }}

```text
{{ database_url }}
```

{% if spec.database == "sqlite" -%}
Setup note: SQLite is local file storage. Back up `./data` if needed.
{% elif spec.database == "turso" -%}
Setup note: Set both `DATABASE_URL` and `TURSO_AUTH_TOKEN` in `.env`.
{% else -%}
Setup note: Use provider-managed credentials and SSL; keep `DATABASE_URL` in secrets.
{% endif %}

See `docs/database.md` before deployment. Keep real credentials in `.env` or in
your deployment platform secrets.

{% if spec.audience == "human-developer" -%}
## Day-1 Workflow (Human Developer)

```bash
uv sync
cp .env.example .env
./scripts/dev.sh
```

Use `AGENTS.md` if you delegate edits to coding agents.
{% elif spec.audience == "ai-agent" -%}
## Agent Workflow

Deterministic command order:

```bash
uv sync
uv run ruff check .
uv run pytest
./scripts/dev.sh
```

Follow edit boundaries and contracts in `AGENTS.md`.
{% else -%}
## Day-1 Workflow (Human Developer)

```bash
uv sync
cp .env.example .env
./scripts/dev.sh
```

## Agent Workflow

Deterministic command order:

```bash
uv sync
uv run ruff check .
uv run pytest
./scripts/dev.sh
```

Follow edit boundaries and contracts in `AGENTS.md`.
{% endif %}

## Cedric Metadata

Cedric stores framework, database, auth, audience, and enabled module information in
`.cedric/project.json`. Run `cedric doctor .` after significant edits to confirm
the project still matches the generated contract.
"""

AGENTS_MD = """# Agent Guide

This project was generated by Cedric.

## Project Contract

- Framework: `{{ spec.framework }}`
- Database preset: `{{ spec.database }}`
- Auth module: `{{ spec.auth }}`
- Template version: `{{ spec.template_version }}`

## Commands

- Install: `uv sync`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Dev server: `./scripts/dev.sh`

## Architecture Notes

- Application code belongs in the framework source package.
- Environment-specific values belong in `.env`, never in source files.
- Database configuration starts in `config/database.py` and `.env.example`.
- Auth endpoint behavior is documented in `docs/auth.md` and `docs/openapi.yaml`.

## Boundaries

- Keep framework code inside the generated application package.
- Update `.cedric/project.json` when changing Cedric-managed modules.
- Preserve OpenAPI compatibility for the auth endpoints documented in `README.md`.
- Run `cedric doctor .` after structural changes.
"""

AUTH_DOC = """# Authentication

The generated auth module uses email and password JWT authentication. FastAPI
projects store users in the selected database by default; other framework
templates are clean starting points that can be connected to durable storage,
email delivery, rate limiting, and audit logging.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Return access and refresh tokens |
| POST | `/auth/refresh` | Rotate or refresh tokens |
| POST | `/auth/logout` | Client-side logout hook |
| GET | `/auth/me` | Return the current user |
| POST | `/auth/password-reset` | Stub for email-based reset flow |

## Production Notes

- Confirm user storage, password reset behavior, and audit needs before production.
- Keep JWT secrets in a secret manager or deployment environment variables.
- Add rate limits to login and password reset endpoints.
- Connect password reset to an email provider before enabling it for users.
- Keep OpenAPI responses aligned with `docs/openapi.yaml`.
"""

DATABASE_DOC = """# Database

Selected database: {{ db.label }}

```text
{{ database_url }}
```

Notes: {{ db.notes }}

## Configuration

- Local defaults are stored in `.env.example`.
- Runtime configuration should be stored in `.env` or deployment secrets.
- Cedric-managed metadata is stored in `.cedric/project.json`.

## Switching Presets

Use this command from the project root:

```bash
cedric add db --database <preset>
```

Supported presets are `sqlite`, `turso`, `postgres-local`, `neon`, and `aws-rds`.
"""

OPENAPI_YAML = """openapi: 3.1.0
info:
  title: {{ spec.name }} API
  version: 0.1.0
paths:
  /auth/register:
    post:
      summary: Register user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RegisterRequest"
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
  /auth/login:
    post:
      summary: Login user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/LoginRequest"
      responses:
        "200":
          description: Token response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TokenResponse"
  /auth/refresh:
    post:
      summary: Refresh tokens
      security:
        - BearerAuth: []
      responses:
        "200":
          description: Token response
  /auth/logout:
    post:
      summary: Logout
      security:
        - BearerAuth: []
      responses:
        "204":
          description: Logged out
  /auth/me:
    get:
      summary: Current user
      security:
        - BearerAuth: []
      responses:
        "200":
          description: Current user
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
  /auth/password-reset:
    post:
      summary: Request password reset
      responses:
        "200":
          description: Password reset flow accepted
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    RegisterRequest:
      type: object
      required: [email, password, name]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          maxLength: 72
        name:
          type: string
    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          maxLength: 72
    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
        refresh_token:
          type: string
        token_type:
          type: string
          example: bearer
    User:
      type: object
      properties:
        email:
          type: string
          format: email
        name:
          type: string
"""

DEVELOPMENT_DOC = """# Development

Use `uv` for dependency management.

## Setup

```bash
uv sync
cp .env.example .env
```

## Daily Commands

```bash
uv run pytest
uv run ruff check .
./scripts/dev.sh
```

## Notes

- Keep local-only values in `.env`.
- Keep generated docs updated when changing public routes.
- Run `cedric doctor .` after structural changes.
"""

DEPLOYMENT_DOC = """# Deployment

This project is generated with local defaults. Review configuration before
deploying it to a shared environment.

## Checklist

- Set a strong `SECRET_KEY`.
- Set `DATABASE_URL` for the selected database provider.
- Store secrets in the deployment platform secret manager.
- Run database migrations before serving traffic.
- Review auth storage and password reset behavior.
- Confirm the OpenAPI endpoint is reachable in the target environment.

## Database

Selected preset: `{{ spec.database }}`

See `docs/database.md` for provider-specific notes.
"""

SETTINGS_TOML = """[app]
name = "{{ spec.name }}"
environment = "local"

[database]
url = "{{ database_url }}"
"""

DEV_SCRIPT = """#!/usr/bin/env sh
set -eu

{% if spec.framework == "fastapi" -%}
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
{% elif spec.framework == "flask" -%}
uv run flask --app app run --debug --host 0.0.0.0 --port 8000
{% else -%}
uv run python manage.py runserver 0.0.0.0:8000
{% endif -%}
"""

SMOKE_TEST = """from pathlib import Path


def test_generated_metadata_exists():
    assert Path(".cedric/project.json").exists()


def test_openapi_contract_documented():
    assert Path("docs/openapi.yaml").read_text().count("/auth/") >= 3
"""

DATABASE_CONFIG = """from __future__ import annotations

import os


DATABASE_URL = os.getenv("DATABASE_URL", "{{ database_url }}")
"""

DOCKERFILE = """FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv sync
COPY . .
CMD ["./scripts/dev.sh"]
"""

DOCKER_COMPOSE = """services:
  app:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - .:/app
{% if spec.database in ["postgres-local"] %}
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
{% endif %}
"""

CI_YML = """name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run pytest
"""

FASTAPI_MAIN = """from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.auth import router as auth_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="{{ spec.name }} API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
"""

FASTAPI_CONFIG = """from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    app_name: str = "{{ spec.name }}"
    database_url: str = "{{ database_url }}"
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60


settings = Settings()
"""

FASTAPI_DB = """from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    database_path = Path(database_url.removeprefix("sqlite:///"))
    if database_path == Path(":memory:"):
        return
    database_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
"""

FASTAPI_AUTH = """from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.config import settings
from app.db import Base, SessionLocal

router = APIRouter()
bearer_scheme = HTTPBearer(scheme_name="BearerAuth")
MAX_BCRYPT_PASSWORD_BYTES = 72


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def password_supported_by_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError("Password must be 72 bytes or fewer")
        return password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_supported_by_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError("Password must be 72 bytes or fewer")
        return password


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    email = payload.get("sub")
    if not isinstance(email, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return user


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    existing_user = db.scalar(select(User).where(User.email == body.email))
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"email": body.email, "name": body.name}


@router.post("/login")
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(body.email)
    return {"access_token": token, "refresh_token": token, "token_type": "bearer"}


@router.post("/refresh")
def refresh(user: Annotated[User, Depends(current_user)]) -> dict[str, str]:
    token = create_token(user.email)
    return {"access_token": token, "refresh_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
def logout() -> None:
    return None


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> dict[str, str]:
    return {"email": user.email, "name": user.name}


@router.post("/password-reset")
def password_reset() -> dict[str, str]:
    return {"status": "password reset flow not configured"}
"""

FLASK_INIT = """from flask import Flask
from flask_smorest import Api

from app.auth import auth_blp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    api = Api(app)
    api.register_blueprint(auth_blp, url_prefix="/auth")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
"""

FLASK_CONFIG = """import os


class Config:
    API_TITLE = "{{ spec.name }} API"
    API_VERSION = "0.1.0"
    OPENAPI_VERSION = "3.1.0"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_JSON_PATH = "openapi.json"
    DATABASE_URL = os.getenv("DATABASE_URL", "{{ database_url }}")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
"""

FLASK_DB = """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Config

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""

FLASK_AUTH = """from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, request
from flask.views import MethodView
from flask_smorest import Blueprint
from passlib.context import CryptContext

auth_blp = Blueprint("auth", __name__, description="Authentication")
passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
users: dict[str, dict[str, str]] = {}


def token_for(email: str) -> str:
    payload = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=60)}
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


@auth_blp.route("/register")
class Register(MethodView):
    def post(self):
        data = request.get_json() or {}
        email = data["email"]
        if email in users:
            return {"message": "Email already registered"}, 409
        users[email] = {
            "email": email,
            "name": data.get("name", ""),
            "password_hash": passwords.hash(data["password"]),
        }
        return {"email": email, "name": users[email]["name"]}, 201


@auth_blp.route("/login")
class Login(MethodView):
    def post(self):
        data = request.get_json() or {}
        user = users.get(data.get("email"))
        if not user or not passwords.verify(data.get("password", ""), user["password_hash"]):
            return {"message": "Invalid credentials"}, 401
        token = token_for(user["email"])
        return {"access_token": token, "refresh_token": token, "token_type": "bearer"}


@auth_blp.route("/refresh")
class Refresh(MethodView):
    def post(self):
        return {"message": "refresh requires token validation wiring"}


@auth_blp.route("/logout")
class Logout(MethodView):
    def post(self):
        return "", 204


@auth_blp.route("/me")
class Me(MethodView):
    def get(self):
        return {"message": "wire JWT validation before production"}


@auth_blp.route("/password-reset")
class PasswordReset(MethodView):
    def post(self):
        return {"status": "password reset flow not configured"}
"""

FLASK_WSGI = """from app import create_app

app = create_app()
"""

DJANGO_MANAGE = """#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""

DJANGO_SETTINGS = """from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="change-me")
DEBUG = env("DEBUG", default=True)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "authentication",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]
WSGI_APPLICATION = "app.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL", default="{{ database_url }}")}

AUTH_USER_MODEL = "authentication.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
SPECTACULAR_SETTINGS = {"TITLE": "{{ spec.name }} API", "VERSION": "0.1.0"}
"""

DJANGO_URLS = """from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
"""

DJANGO_ASGI = """import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
application = get_asgi_application()
"""

DJANGO_WSGI = """import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
application = get_wsgi_application()
"""

DJANGO_AUTH_APPS = """from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"
"""

DJANGO_AUTH_MODELS = """from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email
"""

DJANGO_AUTH_SERIALIZERS = """from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "name", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "token_type": "bearer",
        }
"""

DJANGO_AUTH_VIEWS = """from rest_framework import permissions, status, views
from rest_framework.response import Response

from authentication.serializers import LoginSerializer, RegisterSerializer


class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"email": user.email, "name": user.name}, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class MeView(views.APIView):
    def get(self, request):
        return Response({"email": request.user.email, "name": request.user.name})


class LogoutView(views.APIView):
    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"status": "password reset flow not configured"})
"""

DJANGO_AUTH_URLS = """from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import LoginView, LogoutView, MeView, PasswordResetView, RegisterView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("refresh", TokenRefreshView.as_view(), name="refresh"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("password-reset", PasswordResetView.as_view(), name="password-reset"),
]
"""
