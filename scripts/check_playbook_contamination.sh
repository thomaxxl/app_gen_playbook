#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

failures=0

check_absent() {
  local pattern="$1"
  shift
  local description="$1"
  shift
  if rg -n "$pattern" "$@" >/tmp/check_playbook_contamination.$$ 2>/dev/null; then
    echo "contamination check failed: $description"
    cat /tmp/check_playbook_contamination.$$
    failures=1
  fi
  rm -f /tmp/check_playbook_contamination.$$
}

check_absent \
  '`app/docs/playbook-baseline/current/` is the portable accepted baseline|`app/docs/playbook-baseline/current/` remains the last accepted baseline|`app/docs/playbook-baseline/current/**` is refreshed' \
  'generic playbook docs must not treat app/docs/playbook-baseline/current as canonical' \
  "$repo_root/playbook" \
  "$repo_root/specs" \
  "$repo_root/README.md"

check_absent \
  '`app/docs/change-history/` gains a new accepted change note|updated change history under `app/docs/change-history/`' \
  'generic playbook docs must not treat app/docs/change-history as canonical' \
  "$repo_root/playbook" \
  "$repo_root/specs" \
  "$repo_root/README.md"

check_absent \
  'status surface MUST reopen' \
  'process semantics must not be described as dashboard/status-surface behavior' \
  "$repo_root/playbook"

check_absent \
  'MUST contain the generated-app copy of the approved business-rules catalog' \
  'generic playbook docs must not require an app-local BUSINESS_RULES export by default' \
  "$repo_root/playbook" \
  "$repo_root/specs"

check_absent \
  'run-observer|run_dashboard\.sqlite3|mirrored run-dashboard DB' \
  'shared generated-app README template must stay generic' \
  "$repo_root/templates/app/project/README.app.md"

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

echo "playbook contamination check passed"
