#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: status_report.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

FORMAT="markdown"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --format)
      [[ $# -ge 2 ]] || { echo "error: --format requires a value" >&2; exit 2; }
      FORMAT="$2"
      shift 2
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      exit 2
      ;;
    *)
      echo "error: unexpected argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$FORMAT" in
  markdown|json) ;;
  *)
    echo "error: unsupported format: $FORMAT" >&2
    exit 2
    ;;
esac

python3 "$ROOT/tools/status_report.py" \
  --repo-root "$ROOT" \
  --format "$FORMAT"
