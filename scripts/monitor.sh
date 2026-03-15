#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: monitor.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

JSONL_DIR="${1:-$ROOT/runs/current/evidence/orchestrator/jsonl}"
POLL_SECONDS="${POLL_SECONDS:-1}"

if [[ ! -d "$JSONL_DIR" ]]; then
  echo "error: jsonl directory not found: $JSONL_DIR" >&2
  exit 2
fi

tmpdir="$(mktemp -d)"
seen_file="$tmpdir/seen.txt"
touch "$seen_file"

cleanup() {
  jobs -pr | xargs -r kill 2>/dev/null || true
  rm -rf "$tmpdir"
}
trap cleanup EXIT INT TERM

start_tail() {
  local file="$1"
  local label
  label="$(basename "$file")"

  (
    tail -n +1 -F "$file" 2>/dev/null | while IFS= read -r line; do
      printf '[%s] %s\n' "$label" "$line"
    done
  ) &
}

discover_new_files() {
  local file
  while IFS= read -r file; do
    [[ -n "$file" ]] || continue
    if grep -Fxq "$file" "$seen_file"; then
      continue
    fi
    printf '%s\n' "$file" >> "$seen_file"
    start_tail "$file"
  done < <(find "$JSONL_DIR" -maxdepth 1 -type f -name '*.events.jsonl' | sort)
}

echo "monitoring Codex event streams in: $JSONL_DIR" >&2
echo "press Ctrl-C to stop" >&2

while true; do
  discover_new_files
  sleep "$POLL_SECONDS"
done
