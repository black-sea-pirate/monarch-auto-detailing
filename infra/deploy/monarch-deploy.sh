#!/usr/bin/env bash
set -Eeuo pipefail

readonly APP_DIR="${APP_DIR:-/opt/monarch}"
readonly DEPLOY_REF="${DEPLOY_REF:-origin/production}"
readonly COMPOSE_FILE="${APP_DIR}/compose.yaml"
readonly ENV_FILE="${APP_DIR}/.env"
readonly HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:3000/api/v1/ready}"
readonly HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-30}"
readonly HEALTH_INTERVAL="${HEALTH_INTERVAL:-2}"
readonly LOCK_FILE="${LOCK_FILE:-/tmp/monarch-deploy.lock}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "Another Monarch deployment is already running."
  exit 0
fi

cd "${APP_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing production environment file: ${ENV_FILE}" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to deploy over tracked server-side changes." >&2
  exit 1
fi

previous_commit="$(git rev-parse HEAD)"
git fetch origin production:refs/remotes/origin/production
target_commit="$(git rev-parse "${DEPLOY_REF}")"

if [[ "${previous_commit}" == "${target_commit}" ]]; then
  echo "Production is already at ${target_commit}."
  exit 0
fi

compose_up() {
  sudo docker compose \
    -f "${COMPOSE_FILE}" \
    --env-file "${ENV_FILE}" \
    --profile tunnel \
    up -d --build --remove-orphans

  sudo docker compose \
    -f "${COMPOSE_FILE}" \
    --env-file "${ENV_FILE}" \
    --profile tunnel \
    exec -T nginx nginx -t

  sudo docker compose \
    -f "${COMPOSE_FILE}" \
    --env-file "${ENV_FILE}" \
    --profile tunnel \
    exec -T nginx nginx -s reload
}

wait_until_healthy() {
  local attempt
  for ((attempt = 1; attempt <= HEALTH_ATTEMPTS; attempt++)); do
    if curl --fail --silent --show-error "${HEALTH_URL}" >/dev/null; then
      return 0
    fi
    sleep "${HEALTH_INTERVAL}"
  done
  return 1
}

echo "Deploying ${target_commit} (previous ${previous_commit})."
git switch --detach "${target_commit}"

if compose_up && wait_until_healthy; then
  sudo install -m 0755 \
    "${APP_DIR}/infra/deploy/monarch-deploy.sh" \
    /usr/local/sbin/monarch-deploy
  echo "Deployment succeeded: ${target_commit}."
  exit 0
fi

echo "Deployment failed; rolling back to ${previous_commit}." >&2
git switch --detach "${previous_commit}"
compose_up

if ! wait_until_healthy; then
  echo "Rollback failed health checks and needs manual intervention." >&2
  exit 2
fi

echo "Rollback completed: ${previous_commit}." >&2
exit 1
