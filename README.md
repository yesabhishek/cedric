# Cedric

Cedric is a command line tool for generating clean Python backend projects for
Django, FastAPI, and Flask. It creates a working project structure with database
configuration, JWT authentication endpoints, OpenAPI documentation, Docker files,
CI, tests, development scripts, and metadata that is useful for both developers
and coding agents.

Cedric is built for two common workflows:

- Human developers who want a consistent backend starting point without repeating setup work.
- AI coding agents that need explicit project conventions, commands, and edit boundaries.

## Table Of Contents

- [What Cedric Generates](#what-cedric-generates)
- [Requirements](#requirements)
- [Install Cedric](#install-cedric)
- [Create A Project](#create-a-project)
- [Run Generated Apps Locally](#run-generated-apps-locally)
- [CLI Reference](#cli-reference)
- [Template Options](#template-options)
- [Generated Project Layout](#generated-project-layout)
- [Authentication](#authentication)
- [OpenAPI](#openapi)
- [Agent Metadata](#agent-metadata)
- [Developing Cedric](#developing-cedric)
- [Release Workflow](#release-workflow)
- [Troubleshooting](#troubleshooting)
- [Compatibility](#compatibility)

## What Cedric Generates

Each generated project is intended to run immediately after dependency
installation. Cedric currently generates:

- A Django, FastAPI, or Flask backend.
- A `pyproject.toml` managed with `uv`.
- Database configuration for SQLite, Turso/libSQL, local Postgres, Neon, or AWS RDS.
- JWT authentication endpoints for account creation, login, refresh, logout, current user, and password reset stub.
- OpenAPI documentation in the native style of the selected framework.
- Dockerfile, Docker Compose, GitHub Actions CI, tests, docs, and local development scripts.
- `.cedric/project.json` metadata that records the selected framework, database, auth module, audience, package name, and enabled modules.
- `AGENTS.md` so coding agents have a clear project contract.

Cedric v2 is a rewrite of the older Django-only scaffolder. The active CLI
entrypoint is `cedric init`.

## Requirements

- Python 3.10 or newer.
- `pip`, `pipx`, or another Python package installer.
- `uv` for working inside generated projects.
- Docker if you plan to use generated Docker Compose files.

Install `uv` from the official project if it is not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install Cedric

Install the latest published package:

```bash
pip install --upgrade cedric
```

For isolated CLI usage:

```bash
pipx install cedric
```

Confirm the installed version:

```bash
cedric --version
cedric --help
```

For local development on Cedric itself:

```bash
git clone https://github.com/yesabhishek/cedric.git
cd cedric
uv sync --extra dev
uv run cedric --help
```

## Create A Project

Use the guided wizard:

```bash
cedric init
```

Use non-interactive flags for scripts or repeatable setup:

```bash
cedric init --name my_api --framework fastapi --database sqlite --no-input
```

Create a project in another directory:

```bash
cedric init \
  --name my_service \
  --framework django \
  --database postgres-local \
  --target-dir ~/projects \
  --no-input
```

Replace an existing generated directory:

```bash
cedric init --name my_api --framework fastapi --database sqlite --force --no-input
```

Choose generated README guidance:

```bash
cedric init --name agent_api --audience ai-agent --no-input
```

Supported audience values are:

- `human-developer`: concise day-1 workflow for people.
- `ai-agent`: deterministic command order and agent workflow notes.
- `dual`: includes both human and agent guidance.

## Run Generated Apps Locally

The generated `./scripts/dev.sh` command is the preferred local run path. The
direct framework commands below are useful when you want to run the server
manually or customize host and port flags.

### FastAPI

Create and run:

```bash
cedric init --name my_api --framework fastapi --database sqlite --no-input
cd my_api
uv sync
cp .env.example .env
./scripts/dev.sh
```

Manual run command:

```bash
uv run uvicorn app.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Django

Create and run:

```bash
cedric init --name my_service --framework django --database sqlite --no-input
cd my_service
uv sync
cp .env.example .env
uv run python manage.py migrate
./scripts/dev.sh
```

Manual run command:

```bash
uv run python manage.py runserver
```

Open:

- App: `http://127.0.0.1:8000/`
- Schema: `http://127.0.0.1:8000/api/schema/`

### Flask

Create and run:

```bash
cedric init --name my_gateway --framework flask --database sqlite --no-input
cd my_gateway
uv sync
cp .env.example .env
./scripts/dev.sh
```

Manual run command:

```bash
uv run flask --app app run --debug
```

Open:

- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## CLI Reference

Primary command:

```bash
cedric init [OPTIONS]
```

Options:

| Option | Purpose |
| --- | --- |
| `--name <name>` | Project directory name. Must start with a letter and use only letters, numbers, underscores, or hyphens. |
| `--framework <django|fastapi|flask>` | Framework template to generate. |
| `--database <sqlite|turso|postgres-local|neon|aws-rds>` | Database preset. |
| `--audience <human-developer|ai-agent|dual>` | Controls generated README workflow sections. |
| `--target-dir <path>` | Parent directory where the project should be created. |
| `--force` | Replace an existing project directory. |
| `--no-input` | Use provided values or recommended defaults without prompts. |
| `--help` | Show command help. |

Default non-interactive values:

| Field | Default |
| --- | --- |
| Name | `my_api` |
| Framework | `fastapi` |
| Database | `sqlite` |
| Audience | `human-developer` |

Legacy commands such as `cedric new`, `cedric doctor`, `cedric add`, and
`cedric templates` are intentionally removed. They return migration guidance
instead of mutating projects.

## Template Options

### Frameworks

| Framework | Generated entrypoint | Local server command |
| --- | --- | --- |
| `fastapi` | `app/main.py` | `uv run uvicorn app.main:app --reload` |
| `django` | `manage.py` | `uv run python manage.py runserver` |
| `flask` | `wsgi.py` | `uv run flask --app app run --debug` |

### Database Presets

| Preset | Default URL | Notes |
| --- | --- | --- |
| `sqlite` | `sqlite:///./data/app.db` | Zero-config local file storage. |
| `turso` | `libsql://your-database.turso.io` | SQLite-compatible hosted database. Requires `TURSO_AUTH_TOKEN`. |
| `postgres-local` | `postgresql+psycopg://app:app@localhost:5432/app` | Local Postgres wired to Docker Compose. |
| `neon` | `postgresql+psycopg://user:password@ep-example.neon.tech/app?sslmode=require` | Serverless Postgres. Replace with your Neon pooled URL. |
| `aws-rds` | `postgresql+psycopg://user:password@your-rds-endpoint.amazonaws.com:5432/app` | Managed Postgres. Use SSL and deployment secrets. |

## Generated Project Layout

Typical generated project:

```text
.
|-- .cedric/
|   `-- project.json
|-- .env.example
|-- AGENTS.md
|-- Dockerfile
|-- README.md
|-- app/
|-- config/
|-- docker-compose.yml
|-- docs/
|   |-- auth.md
|   |-- database.md
|   |-- deployment.md
|   |-- development.md
|   `-- openapi.yaml
|-- migrations/
|-- pyproject.toml
|-- scripts/
|   `-- dev.sh
`-- tests/
```

Django projects also include `manage.py` and an `authentication/` app.
Flask projects include `wsgi.py`.

## Authentication

Cedric scaffolds the same auth surface across supported frameworks:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Create an account. |
| `POST` | `/auth/login` | Return access and refresh tokens. |
| `POST` | `/auth/refresh` | Refresh tokens. |
| `POST` | `/auth/logout` | Logout hook. |
| `GET` | `/auth/me` | Return the current authenticated user. |
| `POST` | `/auth/password-reset` | Stub for a future reset flow. |

FastAPI projects use direct `bcrypt` hashing and HTTP Bearer auth in Swagger.
Users are stored in the selected database by default. Passwords longer than
bcrypt's 72-byte limit are rejected with validation errors instead of server
errors.

The generated auth is a practical starting point, not a full identity platform.
Before production, review:

- Rate limits for login and password reset.
- Email delivery for password reset.
- Secret management for JWT signing keys.
- Audit logging and account lifecycle requirements.

## OpenAPI

Generated projects expose framework-native schema endpoints:

| Framework | Schema endpoint | Interactive docs |
| --- | --- | --- |
| FastAPI | `/openapi.json` | `/docs` |
| Django | `/api/schema/` | Depends on how you serve drf-spectacular views. |
| Flask | `/openapi.json` | Depends on flask-smorest UI configuration. |

Every project also includes `docs/openapi.yaml` as a concise contract reference
for the generated auth endpoints.

## Agent Metadata

Cedric writes files that help coding agents and humans understand the generated
project:

- `AGENTS.md`: commands, architecture notes, and edit boundaries.
- `.cedric/project.json`: framework, database, auth module, audience, package name, template version, and enabled modules.
- `docs/`: notes for auth, database setup, development, deployment, and OpenAPI behavior.

Use these files before making large automated edits. They are intended to reduce
guesswork and keep generated projects consistent.

## Developing Cedric

Install development dependencies:

```bash
uv sync --extra dev
```

Run checks:

```bash
uv run ruff check .
uv run pytest
uv build
uvx twine check dist/*
```

Run the local reinstall smoke workflow:

```bash
./scripts/reinstall_local_and_test.sh
```

That script builds the local package, reinstalls it with `pipx`, generates sample
projects, and HTTP-tests generated FastAPI auth.

## Release Workflow

Releases are published from GitHub tags through `.github/workflows/release.yml`.
The release workflow:

1. Builds the source distribution and wheel.
2. Runs lint, tests, and `twine check`.
3. Creates a GitHub Release with artifacts attached.
4. Publishes to PyPI using the protected `pypi` environment.

See `RELEASE.md` for the operational release checklist.

## Troubleshooting

### `ModuleNotFoundError: No module named 'bcrypt'`

You are probably running an older generated app or a stale virtual environment.
Regenerate the app with the latest Cedric and sync dependencies:

```bash
pip install --upgrade cedric
cedric init --name my_api --framework fastapi --database sqlite --force --no-input
cd my_api
uv sync
uv run python -c "import bcrypt; print(bcrypt.__version__)"
```

### `cedric --version` changed but my generated app did not

Cedric copies template files into generated projects. Updating Cedric does not
rewrite existing apps. Regenerate with `--force` or manually apply the template
change to the existing project.

### My project is inside `.Trash`

Move or regenerate the project outside `.Trash`. macOS may restrict access to
files in Trash, and development tools may behave inconsistently there.

### `cedric new` or `cedric doctor` no longer works

Use `cedric init`. Older lifecycle commands were removed in the current CLI.

## Compatibility

- Current primary command: `cedric init`.
- Deprecated compatibility entrypoint: `cedric-setup`, which exits with migration guidance.
- Removed commands: `cedric new`, `cedric doctor`, `cedric add`, `cedric templates`.
- Replaced package architecture: the old Django-only `src` package was replaced by the v2 `cedric` package.

## License

Cedric is distributed under the GPL-3.0-only license. See `LICENSE` for details.
