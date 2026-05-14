# Contributing

Thanks for helping improve Cedric. This project is a Python CLI and template
generator, so changes should be tested both as package code and as generated
project output.

## Development Setup

```bash
git clone https://github.com/yesabhishek/cedric.git
cd cedric
uv sync --extra dev
```

## Local Checks

Run these before opening a pull request:

```bash
uv run pytest
uv run ruff check .
uv build
```

## Template Changes

When editing generated project templates:

- Generate at least one project for each affected framework.
- Run `cedric doctor <project>` against generated output.
- Keep generated docs aligned with generated files.
- Avoid hard-coded secrets, personal paths, or environment-specific credentials.

## CLI Changes

When editing commands:

- Keep commands scriptable with explicit flags.
- Keep prompt-driven behavior optional.
- Preserve clear error messages for humans and AI agents.
- Add tests for successful and failing command paths.

## Documentation Standards

- Use clear, direct language.
- Do not use emojis.
- Do not use em dashes.
- Prefer examples that users can run without extra context.
