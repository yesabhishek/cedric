# Cedric

Cedric is a command line tool for creating clean Python backend projects for
Django, FastAPI, and Flask. It generates a professional project structure with
database configuration, JWT authentication endpoints, OpenAPI documentation,
Docker files, CI, tests, and agent-ready project metadata.

Cedric is designed for two workflows:

- Human developers who want a consistent project foundation without repetitive setup.
- AI coding agents that need explicit conventions, safe edit boundaries, and
  machine-readable project metadata.

## Status

Cedric v2 is a full rewrite of the original Django-only scaffolder. The new CLI
uses `cedric` as the primary command and keeps `cedric-setup` only as a
deprecated compatibility entry point.

## Features

- Generate Django, FastAPI, or Flask projects from one CLI.
- Choose SQLite, Turso/libSQL, local Postgres, Neon Postgres, or AWS RDS Postgres.
- Create a `uv`-based Python project with `pyproject.toml` and a starter lockfile.
- Include JWT auth scaffolding with register, login, refresh, logout, me, and
  password reset endpoints.
- Include OpenAPI documentation suited to each framework.
- Generate Docker, Docker Compose, GitHub Actions CI, tests, scripts, and docs.
- Write `.cedric/project.json` so Cedric and AI agents can understand the project.
- Provide lifecycle commands for refreshing DB, auth, Docker, and CI files.

## Requirements

- Python 3.10 or newer.
- `pipx`, `pip`, or another Python package installer.
- `uv` is recommended for working inside generated projects.

## Installation

Install the published package:

```bash
pip install cedric
```

For isolated CLI usage:

```bash
pipx install cedric
```

For local development on Cedric itself:

```bash
git clone https://github.com/yesabhishek/cedric.git
cd cedric
uv sync --extra dev
uv run cedric --help
```

## Run Locally By Framework

FastAPI:

```bash
cedric init --name my_api --framework fastapi --database sqlite --no-input
cd my_api
uv sync
cp .env.example .env
./scripts/dev.sh
```

Manual FastAPI run command:

```bash
uv run uvicorn app.main:app --reload
```

Open Swagger UI at `/docs` or the schema at `/openapi.json`.

Django:

```bash
cedric init --name my_service --framework django --database sqlite --no-input
cd my_service
uv sync
cp .env.example .env
uv run python manage.py migrate
./scripts/dev.sh
```

Manual Django run command:

```bash
uv run python manage.py runserver
```

Open the app at `/` and the schema at `/api/schema/`.

Flask:

```bash
cedric init --name my_gateway --framework flask --database sqlite --no-input
cd my_gateway
uv sync
cp .env.example .env
./scripts/dev.sh
```

Manual Flask run command:

```bash
uv run flask --app app run --debug
```

Open the schema at `/openapi.json`.

## CLI Reference

Create a project:

```bash
cedric new <name> --framework <django|fastapi|flask> --database <preset>
```

Useful options:

- `--target-dir <path>` writes the project into another directory.
- `--force` replaces an existing project directory.
- `--no-input` disables prompts for scripts and AI agents.

Manage a generated project:

```bash
cedric doctor .
cedric add db --database neon
cedric add auth
cedric add docker
cedric add ci
cedric templates list
```

## Supported Templates

Frameworks:

- `django`
- `fastapi`
- `flask`

Database presets:

- `sqlite`: local file-backed SQLite.
- `turso`: Turso/libSQL SQLite-compatible hosted database.
- `postgres-local`: local Postgres with Docker Compose support.
- `neon`: Neon hosted Postgres.
- `aws-rds`: AWS RDS Postgres.

Auth module:

- `jwt`: email and password JWT authentication.

## Generated Project Layout

Cedric projects include:

```text
.
|-- .cedric/project.json
|-- .env.example
|-- AGENTS.md
|-- Dockerfile
|-- README.md
|-- app/
|-- config/
|-- docker-compose.yml
|-- docs/
|-- migrations/
|-- pyproject.toml
|-- scripts/
|-- tests/
`-- uv.lock
```

Framework-specific files are generated where appropriate. Django projects also
include `manage.py` and an `authentication/` app.

## Authentication API

The default auth module documents and scaffolds these endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Return access and refresh tokens |
| `POST` | `/auth/refresh` | Refresh tokens |
| `POST` | `/auth/logout` | Logout hook |
| `GET` | `/auth/me` | Return the current user |
| `POST` | `/auth/password-reset` | Password reset integration stub |

The generated auth code is a solid starting point, not a complete identity
platform. Replace in-memory examples with durable user storage before production.

## OpenAPI Support

- FastAPI projects use native OpenAPI at `/openapi.json`.
- Django projects use Django REST Framework with drf-spectacular at `/api/schema/`.
- Flask projects use flask-smorest at `/openapi.json`.

Each project also includes `docs/openapi.yaml` as a concise contract reference
for the generated auth surface.

## Working With AI Agents

Every generated project includes:

- `AGENTS.md` with commands, architecture notes, and edit boundaries.
- `.cedric/project.json` with framework, database, auth, template version, and
  enabled module metadata.
- Docs that describe auth, database configuration, and OpenAPI expectations.

Use `cedric doctor .` before and after large automated edits to confirm that the
project still matches Cedric expectations.

## Development

Run checks for Cedric itself:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv build
```

The test suite covers project spec validation, CLI commands, generated file
trees, database switching, and `doctor` failure modes.

## Releases

Releases are published through GitHub Releases and then to production PyPI after
approval in the protected `pypi` GitHub environment. See `RELEASE.md` for the
full branch, pull request, sanity check, tag, and release workflow.

## Compatibility

The old `cedric-setup` command is deprecated. Use:

```bash
cedric new <name>
```

The v1 Django-only `src` package has been replaced by the v2 `cedric` package.

## License

Cedric is distributed under the GPL-3.0-only license. See `LICENSE` for details.
