#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
if [[ "$GIT_ROOT" != "$ROOT" ]]; then
  echo "error: save_run.sh must run from the playbook repo: $ROOT" >&2
  exit 2
fi

SAVE_ROOT="${PLAYBOOK_SAVE_ROOT:-$ROOT/saved}"
RUN_CURRENT="$ROOT/runs/current"
APP_DIR="$ROOT/app"

clean_after=0
archive_label=""

usage() {
  cat <<'EOF'
Usage: ./scripts/save_run.sh [--name LABEL] [--clean]

Archives the current local run workspace and generated app under saved/<timestamp>[-label]/.

Options:
  --name LABEL   append a readable label to the archive directory name
  --clean        run scripts/clean.sh after the archive succeeds
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      if [[ $# -lt 2 ]]; then
        echo "error: --name requires a label" >&2
        exit 2
      fi
      archive_label="$2"
      shift 2
      ;;
    --clean)
      clean_after=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unexpected argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

saved_any=0
timestamp="$(date -u +%Y%m%d-%H%M%SZ)"
safe_label="$(printf '%s' "$archive_label" | tr ' /:' '---' | tr -cd 'A-Za-z0-9._-')"
archive_name="$timestamp"
if [[ -n "$safe_label" ]]; then
  archive_name="${archive_name}-${safe_label}"
fi

archive_dir="$SAVE_ROOT/$archive_name"
if [[ -e "$archive_dir" ]]; then
  echo "error: archive destination already exists: $archive_dir" >&2
  exit 1
fi

mkdir -p "$archive_dir"

if [[ -d "$RUN_CURRENT" ]]; then
  cp -a "$RUN_CURRENT" "$archive_dir/runs-current"
  saved_any=1
fi

if [[ -d "$APP_DIR" ]]; then
  cp -a "$APP_DIR" "$archive_dir/app"
  saved_any=1
fi

if [[ "$saved_any" -eq 0 ]]; then
  rmdir "$archive_dir"
  echo "error: nothing to save; neither runs/current nor app/ exists" >&2
  exit 1
fi

cat >"$archive_dir/README.md" <<EOF
# Saved Playbook Workspace

- saved_at_utc: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`
- source_repo: \`$ROOT\`
- source_run_dir: \`$RUN_CURRENT\`
- source_app_dir: \`$APP_DIR\`
- archive_label: \`${archive_label:-none}\`
- clean_after_save: \`$([[ "$clean_after" -eq 1 ]] && echo yes || echo no)\`

Contents:

- \`runs-current/\` when a local run existed
- \`app/\` when a local generated app existed
EOF

echo "saved workspace snapshot to $archive_dir"

if [[ "$clean_after" -eq 1 ]]; then
  "$SCRIPT_DIR/clean.sh"
  echo "cleaned workspace after saving snapshot"
fi
