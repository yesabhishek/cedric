# Release Process

This guide describes how to publish Cedric through a reviewed GitHub pull request
and a GitHub Release. Production PyPI publishing is handled by GitHub Actions
through a protected `pypi` environment.

## Required GitHub Settings

Before the first v2 release:

- Create a GitHub environment named `pypi`.
- Add required reviewer approval to the `pypi` environment.
- Add an environment secret named `PYPI_API_TOKEN`.
- Store only the PyPI API token in that secret.
- Do not store PyPI tokens in `.env`, `.pypirc`, workflow YAML, docs, or source files.

If a token has been pasted into chat or another non-secret location, revoke it in
PyPI and create a fresh project-scoped token before adding it to GitHub.

## 1. Prepare a Branch

From a clean local checkout:

```bash
git checkout -b codex/cedric-v2-release
git status
```

Review all changed files before staging:

```bash
git diff --stat
git diff
```

## 2. Run Local Checks

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
uv build
uvx twine check dist/*
```

Remove local build artifacts before committing:

```bash
rm -rf dist .ruff_cache .pytest_cache
find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

## 3. Commit and Push

```bash
git add .
git commit -m "Release Cedric v2 CLI rewrite"
git push -u origin codex/cedric-v2-release
```

## 4. Open a Pull Request

Open a pull request from `codex/cedric-v2-release` into `main`.

Use the pull request template checklist. Ask Codex to review the PR for:

- CLI behavior and command ergonomics.
- Generated Django, FastAPI, and Flask project structure.
- Auth and OpenAPI documentation consistency.
- GitHub Actions release safety.
- Packaging metadata and compatibility.

Wait for the `Sanity` workflow to pass before merging.

## 5. Create a Release Tag

After the pull request is merged into `main`:

```bash
git checkout main
git pull origin main
git tag v2.0.0
git push origin v2.0.0
```

The `Release` workflow will:

- Build the package.
- Validate package metadata with `twine check`.
- Create a GitHub Release with the source distribution and wheel attached.
- Wait for approval in the protected `pypi` environment.
- Publish `cedric` to production PyPI with `PYPI_API_TOKEN`.

## 6. Manual Release Option

The `Release` workflow also supports manual dispatch from GitHub Actions.
Provide the release tag, for example:

```text
v2.0.0
```

Prefer tag-based releases for normal publishing.

## 7. Verify PyPI

After the `publish-pypi` job succeeds:

```bash
python -m pip install --upgrade cedric==2.0.0
cedric --version
cedric templates list
```

## Current Release Candidate

- Version: `2.0.0`
- Primary command: `cedric`
- Deprecated compatibility command: `cedric-setup`
- Release mechanism: GitHub Release with generated notes and attached Python artifacts.
- PyPI mechanism: protected GitHub environment with `PYPI_API_TOKEN`.
- TestPyPI: skipped for this release.
