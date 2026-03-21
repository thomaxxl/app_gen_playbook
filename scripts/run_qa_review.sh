#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_ROOT="$ROOT/runs/current"
QA_MANIFEST_REL="runs/current/evidence/ui-previews/qa-manifest.md"
QA_OUTPUT_DIR_REL="runs/current/evidence/ui-previews/qa"
REVIEW_PLAN_REL="runs/current/evidence/quality/review-plan.json"
CAPTURE_ONLY=0
AGENT_ONLY=0

usage() {
  cat <<'EOF'
Usage: scripts/run_qa_review.sh [--capture-only] [--agent-only]

Runs the final QA screenshot capture and then dispatches a single QA review
turn against runs/current/. This can also be used retroactively on an existing
current run.

Options:
  --capture-only   Only capture/update the QA screenshots and manifest.
  --agent-only     Skip screenshot capture and only run the QA agent once.
  -h, --help       Show this help text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --capture-only)
      CAPTURE_ONLY=1
      ;;
    --agent-only)
      AGENT_ONLY=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$CAPTURE_ONLY" -eq 1 && "$AGENT_ONLY" -eq 1 ]]; then
  echo "error: --capture-only and --agent-only cannot be combined" >&2
  exit 2
fi

if [[ ! -d "$RUN_ROOT" ]]; then
  echo "error: missing runs/current/" >&2
  exit 1
fi

if [[ ! -f "$ROOT/app/frontend/package.json" ]]; then
  echo "error: missing app/frontend/package.json" >&2
  exit 1
fi

mkdir -p "$(dirname "$ROOT/$QA_MANIFEST_REL")" "$ROOT/$QA_OUTPUT_DIR_REL"

write_blocked_manifest() {
  local capture_result="$1"
  cat > "$ROOT/$QA_MANIFEST_REL" <<EOF
# QA Screenshot Manifest

capture_status: environment-blocked
- command: \`npm run capture:qa-screenshots\`
- reviewed_surfaces:
- capture_failures:
  - $capture_result
- review_conclusion: QA screenshot capture did not complete; treat this as a QA blocker unless the environment restriction is explicitly resolved.
EOF
}

capture_result="capture step skipped"
if [[ "$AGENT_ONLY" -eq 0 ]]; then
  set +e
  (
    cd "$ROOT/app/frontend"
    REVIEW_PLAN_PATH="$ROOT/$REVIEW_PLAN_REL" \
    QA_SCREENSHOT_OUTPUT_DIR="$ROOT/$QA_OUTPUT_DIR_REL" \
    QA_SCREENSHOT_MANIFEST="$ROOT/$QA_MANIFEST_REL" \
    npm run capture:qa-screenshots
  )
  capture_status=$?
  set -e
  if [[ $capture_status -eq 0 ]]; then
    capture_result="capture succeeded via npm run capture:qa-screenshots"
  else
    capture_result="capture failed with exit status $capture_status via npm run capture:qa-screenshots"
    if [[ ! -f "$ROOT/$QA_MANIFEST_REL" ]]; then
      write_blocked_manifest "$capture_result"
    fi
  fi
fi

if [[ "$CAPTURE_ONLY" -eq 1 ]]; then
  printf '%s\n' "$ROOT/$QA_MANIFEST_REL"
  exit 0
fi

exec python3 "$ROOT/tools/run_qa_review_once.py" \
  --repo-root "$ROOT" \
  --qa-manifest "$QA_MANIFEST_REL" \
  --capture-result "$capture_result"
