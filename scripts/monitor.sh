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
MONITOR_TAIL_LINES="${MONITOR_TAIL_LINES:-100}"

if [[ ! -d "$JSONL_DIR" ]]; then
  echo "error: jsonl directory not found: $JSONL_DIR" >&2
  exit 2
fi

if ! [[ "$MONITOR_TAIL_LINES" =~ ^[0-9]+$ ]] || [[ "$MONITOR_TAIL_LINES" -le 0 ]]; then
  echo "error: MONITOR_TAIL_LINES must be a positive integer: $MONITOR_TAIL_LINES" >&2
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

list_jsonl_files() {
  find "$JSONL_DIR" -maxdepth 1 -type f -name '*.events.jsonl' -printf '%T@ %p\n' | sort -n | cut -d' ' -f2-
}

start_tail() {
  local file="$1"
  local initial_lines="${2:-0}"
  local label
  label="$(basename "$file")"

  (
    tail -n "$initial_lines" -F "$file" 2>/dev/null | while IFS= read -r line; do
      printf '[%s] %s\n' "$label" "$line"
    done
  ) &
}

prime_existing_files() {
  mapfile -t files < <(list_jsonl_files)
  if [[ "${#files[@]}" -eq 0 ]]; then
    return
  fi

  python3 - "$MONITOR_TAIL_LINES" "${files[@]}" <<'PY'
import collections
import pathlib
import sys

limit = int(sys.argv[1])
files = sys.argv[2:]
lines = collections.deque(maxlen=limit)
for file_path in files:
    label = pathlib.Path(file_path).name
    try:
        with open(file_path, encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                lines.append(f"[{label}] {raw_line.rstrip()}")
    except FileNotFoundError:
        continue

for line in lines:
    print(line)
PY

  local file
  for file in "${files[@]}"; do
    [[ -n "$file" ]] || continue
    printf '%s\n' "$file" >> "$seen_file"
    start_tail "$file" 0
  done
}

discover_new_files() {
  local file
  [[ -f "$seen_file" ]] || return 0
  while IFS= read -r file; do
    [[ -n "$file" ]] || continue
    [[ -f "$seen_file" ]] || return 0
    if grep -Fxq "$file" "$seen_file"; then
      continue
    fi
    printf '%s\n' "$file" >> "$seen_file"
    start_tail "$file" 0
  done < <(list_jsonl_files)
}

echo "monitoring Codex event streams in: $JSONL_DIR" >&2
echo "showing last $MONITOR_TAIL_LINES lines across existing streams, then following new output" >&2
echo "press Ctrl-C to stop" >&2

prime_existing_files

while true; do
  discover_new_files
  sleep "$POLL_SECONDS"
done
