from __future__ import annotations

FRAMEWORKS = ("django", "fastapi", "flask")

DATABASES = {
    "sqlite": {
        "label": "SQLite local",
        "url": "sqlite:///./data/app.db",
        "notes": "Zero-config local database stored inside ./data.",
    },
    "turso": {
        "label": "Turso/libSQL",
        "url": "libsql://your-database.turso.io",
        "notes": "SQLite-compatible hosted database. Requires TURSO_AUTH_TOKEN.",
    },
    "postgres-local": {
        "label": "Postgres local",
        "url": "postgresql+psycopg://app:app@localhost:5432/app",
        "notes": "Local Postgres, wired to docker-compose by default.",
    },
    "neon": {
        "label": "Neon Postgres",
        "url": "postgresql+psycopg://user:password@ep-example.neon.tech/app?sslmode=require",
        "notes": "Serverless Postgres. Replace DATABASE_URL with the Neon pooled URL.",
    },
    "aws-rds": {
        "label": "AWS RDS Postgres",
        "url": "postgresql+psycopg://user:password@your-rds-endpoint.amazonaws.com:5432/app",
        "notes": "Managed Postgres. Use SSL and secrets management in deployed environments.",
    },
}

AUTH_MODULES = {
    "jwt": "Email/password JWT APIs: register, login, refresh, logout, me, password reset stub."
}

TEMPLATE_VERSION = "2.0.0"
