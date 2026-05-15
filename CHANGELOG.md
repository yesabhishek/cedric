# Changelog

All notable changes to Cedric are documented here.

## 2.0.2

### Added

- Added a guided `cedric init` workflow with audience-specific generated README sections.
- Added local run instructions for Django, FastAPI, and Flask projects.
- Added a local reinstall smoke script that builds, reinstalls, generates, and HTTP-tests FastAPI auth.

### Fixed

- Fixed generated FastAPI auth for `bcrypt` 5 by replacing Passlib with direct bcrypt hashing.
- Switched generated FastAPI Swagger auth to HTTP Bearer tokens.
- Stored generated FastAPI users in SQLite-backed SQLAlchemy tables instead of process memory.
- Updated generated FastAPI OpenAPI docs to declare Bearer auth on protected endpoints.
- Updated GitHub sanity workflow to use `cedric init`.

## 2.0.1

### Fixed

- Fixed `cedric --version` so it prints the CLI version without requiring a subcommand.

## 2.0.0

### Added

- New `cedric` CLI built with Typer and Rich.
- Project generation for Django, FastAPI, and Flask.
- Database presets for SQLite, Turso/libSQL, local Postgres, Neon, and AWS RDS.
- JWT authentication scaffolding with documented auth endpoints.
- OpenAPI documentation for generated projects.
- Docker, Docker Compose, GitHub Actions CI, tests, and `uv` project files.
- `.cedric/project.json` metadata for lifecycle commands and AI agents.
- `cedric doctor` validation command.
- `cedric add db`, `cedric add auth`, `cedric add docker`, and `cedric add ci`.

### Changed

- Replaced the legacy Django-only `src` package with the v2 `cedric` package.
- Replaced `setup.py` packaging with `pyproject.toml`.
- Deprecated `cedric-setup` in favor of `cedric new <name>`.

### Removed

- Removed hard-coded database credentials from generated projects.
- Removed unsafe shell-based Django project mutation from the old scaffolder.
