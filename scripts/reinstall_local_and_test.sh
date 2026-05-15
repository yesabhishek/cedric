#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[1/7] Running repository checks"
uv run pytest -q
uv run ruff check .

echo "[2/7] Building local package"
rm -rf dist build ./*.egg-info
uv build

WHEEL_PATH="$(ls -1t dist/cedric-*.whl | head -n1)"
if [[ -z "${WHEEL_PATH}" ]]; then
  echo "No wheel found in dist/"
  exit 1
fi

echo "[3/7] Reinstalling in pipx from local wheel: ${WHEEL_PATH}"
pipx uninstall cedric >/dev/null 2>&1 || true
pipx install "${WHEEL_PATH}" --force

echo "[4/7] Validating basic CLI availability"
cedric --version
cedric --help >/dev/null

TMP_BASE="$(mktemp -d)"
SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  rm -rf "${TMP_BASE}"
}
trap cleanup EXIT

free_port() {
  uv run python - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

wait_for_health() {
  local url="$1"
  for _ in {1..60}; do
    if curl -fsS "${url}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for ${url}/health"
  return 1
}

echo "[5/7] Smoke test: recommended defaults"
cedric init --no-input --target-dir "${TMP_BASE}" --name smoke_default
test -d "${TMP_BASE}/smoke_default"

echo "[5a/7] Smoke test: generated FastAPI auth works"
FASTAPI_APP="${TMP_BASE}/smoke_default"
grep -q '"bcrypt>=5.0"' "${FASTAPI_APP}/pyproject.toml"
! grep -R "passlib\\|OAuth2PasswordBearer\\|CryptContext" "${FASTAPI_APP}/app/auth.py"
grep -q "HTTPBearer" "${FASTAPI_APP}/app/auth.py"
pushd "${FASTAPI_APP}" >/dev/null
uv sync
PORT="$(free_port)"
uv run uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" >server.log 2>&1 &
SERVER_PID="$!"
wait_for_health "http://127.0.0.1:${PORT}"

EMAIL="smoke-$(date +%s)@example.com"
REGISTER_STATUS="$(
  curl -sS -o /tmp/cedric-register.json -w '%{http_code}' \
    -X POST "http://127.0.0.1:${PORT}/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"short-password\",\"name\":\"Smoke User\"}"
)"
test "${REGISTER_STATUS}" = "201"

LOGIN_JSON="$(
  curl -sS \
    -X POST "http://127.0.0.1:${PORT}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"short-password\"}"
)"
TOKEN="$(printf '%s' "${LOGIN_JSON}" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
test -n "${TOKEN}"

ME_STATUS="$(
  curl -sS -o /tmp/cedric-me.json -w '%{http_code}' \
    "http://127.0.0.1:${PORT}/auth/me" \
    -H "Authorization: Bearer ${TOKEN}"
)"
test "${ME_STATUS}" = "200"

curl -fsS "http://127.0.0.1:${PORT}/openapi.json" \
  | uv run python -c 'import json,sys; schemes=json.load(sys.stdin)["components"]["securitySchemes"]; assert schemes == {"BearerAuth": {"type": "http", "scheme": "bearer"}}'

kill "${SERVER_PID}" >/dev/null 2>&1 || true
wait "${SERVER_PID}" >/dev/null 2>&1 || true
SERVER_PID=""
popd >/dev/null

echo "[6/7] Smoke test: explicit framework/database"
cedric init --no-input --target-dir "${TMP_BASE}" --name smoke_django --framework django --database postgres-local
test -f "${TMP_BASE}/smoke_django/manage.py"

echo "[7/7] Legacy compatibility checks"
set +e
cedric new test-app >/dev/null 2>&1
NEW_EXIT=$?
cedric doctor . >/dev/null 2>&1
DOCTOR_EXIT=$?
cedric add db postgres >/dev/null 2>&1
ADD_EXIT=$?
cedric templates list >/dev/null 2>&1
TEMPLATES_EXIT=$?
cedric-setup >/dev/null 2>&1
SETUP_EXIT=$?
set -e

if [[ "$NEW_EXIT" -eq 0 || "$DOCTOR_EXIT" -eq 0 || "$ADD_EXIT" -eq 0 || "$TEMPLATES_EXIT" -eq 0 ]]; then
  echo "One or more removed legacy commands unexpectedly succeeded."
  exit 1
fi

if [[ "$SETUP_EXIT" -eq 0 ]]; then
  echo "cedric-setup unexpectedly succeeded."
  exit 1
fi

echo "Local reinstall + smoke test completed successfully."
