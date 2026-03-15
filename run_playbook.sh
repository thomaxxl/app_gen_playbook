#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 path/to/input.md" >&2
  exit 1
fi

if [[ "$1" != *.md ]]; then
  echo "error: input must be a markdown file: $1" >&2
  exit 1
fi

if [[ ! -f "$1" ]]; then
  echo "error: input file not found: $1" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
if [[ "$ROOT" != "$SCRIPT_DIR" ]]; then
  echo "error: run_playbook.sh must run from the playbook repo root: $SCRIPT_DIR" >&2
  exit 1
fi

INPUT_SRC="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
STATE="$ROOT/runs/current"
ROLE_STATE="$STATE/role-state"
EVIDENCE="$STATE/evidence/orchestrator"

python3 "$ROOT/tools/reset_current_run.py" --repo-root "$ROOT" >/dev/null

mkdir -p "$EVIDENCE" "$ROLE_STATE/product_manager/inbox"
cp "$INPUT_SRC" "$STATE/input.md"
cp "$INPUT_SRC" "$ROLE_STATE/product_manager/inbox/INPUT.md"

declare -A ROLE_DIR=(
  [product-manager]="product_manager"
  [architect]="architect"
  [frontend]="frontend"
  [backend]="backend"
)

declare -A ROLE_FILE=(
  [product-manager]="playbook/roles/product-manager.md"
  [architect]="playbook/roles/architect.md"
  [frontend]="playbook/roles/frontend.md"
  [backend]="playbook/roles/backend.md"
)

ROLES=(product-manager architect frontend backend)

oldest_inbox_item() {
  local role_dir="$1"
  find "$role_dir/inbox" -maxdepth 1 -type f -name '*.md' | sort | head -n 1
}

run_role_once() {
  local display_role="$1"
  local runtime_role="$2"
  local role_file="$3"
  local role_dir="$ROLE_STATE/$runtime_role"

  local msg
  msg="$(oldest_inbox_item "$role_dir")"
  [[ -n "${msg:-}" ]] || return 1

  local msg_base
  msg_base="$(basename "$msg" .md)"
  local prompt_file="$EVIDENCE/${runtime_role}-${msg_base}-prompt.md"
  local result_file="$EVIDENCE/${runtime_role}-${msg_base}-result.md"
  local json_file="$EVIDENCE/${runtime_role}-${msg_base}-events.jsonl"
  local snapshot_file="$EVIDENCE/${runtime_role}-${msg_base}-snapshot.json"
  local validation_file="$EVIDENCE/${runtime_role}-${msg_base}-validation.md"

  python3 "$ROOT/tools/validate_role_diff.py" snapshot \
    --repo-root "$ROOT" \
    --output "$snapshot_file" >/dev/null

  python3 "$ROOT/tools/build_role_prompt.py" \
    --repo-root "$ROOT" \
    --display-role "$display_role" \
    --runtime-role "$runtime_role" \
    --role-file "$role_file" \
    --message "$msg" \
    > "$prompt_file"

  (
    cd "$ROOT"
    codex exec \
      --full-auto \
      --json \
      --output-last-message "$result_file" \
      - < "$prompt_file" \
      > "$json_file"
  )

  python3 "$ROOT/tools/validate_role_diff.py" validate \
    --repo-root "$ROOT" \
    --runtime-role "$runtime_role" \
    --snapshot "$snapshot_file" \
    --evidence-out "$validation_file"

  if [[ -f "$msg" ]]; then
    echo "error: role $runtime_role left inbox message in place: $msg" >&2
    exit 1
  fi

  if [[ ! -f "$role_dir/context.md" ]]; then
    echo "error: role $runtime_role did not create or update context.md" >&2
    exit 1
  fi

  return 0
}

while true; do
  did_work=0

  for display_role in "${ROLES[@]}"; do
    runtime_role="${ROLE_DIR[$display_role]}"
    role_file="${ROLE_FILE[$display_role]}"

    if run_role_once "$display_role" "$runtime_role" "$role_file"; then
      did_work=1
    fi
  done

  if python3 "$ROOT/tools/check_completion.py" --repo-root "$ROOT"; then
    touch "$STATE/APP_DONE"
    echo "playbook run complete"
    exit 0
  fi

  if [[ "$did_work" -eq 0 ]]; then
    sleep 2
  fi
done
