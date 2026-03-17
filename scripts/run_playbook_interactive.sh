#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_PLAYBOOK="$SCRIPT_DIR/run_playbook.sh"

if [[ ! -x "$RUN_PLAYBOOK" ]]; then
  echo "error: runnable not found: $RUN_PLAYBOOK" >&2
  exit 2
fi

if [[ ! -t 0 || ! -t 1 ]]; then
  echo "error: interactive mode requires a TTY (stdin/stdout must be interactive)" >&2
  echo "Use $RUN_PLAYBOOK directly for non-interactive automation." >&2
  exit 2
fi

ask() {
  local prompt="$1"
  local default="$2"
  local value=""
  read -r -p "$prompt [$default]: " value < /dev/tty
  value="${value:-$default}"
  printf '%s\n' "$value"
}

ask_yes_no() {
  local prompt="$1"
  local default="$2"
  local value
  value="$(ask "$prompt" "$default")"
  case "${value,,}" in
    y|yes)
      printf '%s\n' yes
      ;;
    n|no)
      printf '%s\n' no
      ;;
    *)
      printf '%s\n' invalid
      ;;
  esac
}

pick_mode() {
  local mode
  while true; do
    mode="$(ask "Playbook mode (new, iterate, hotfix)" "new")"
    case "$mode" in
      new|iterate|hotfix) break ;;
      *)
        echo "Unsupported mode: $mode"
        ;;
    esac
  done
  printf '%s\n' "$mode"
}

pick_role() {
  local role
  while true; do
    role="$(ask "Target role for resume (empty to let runner decide)" "")"
    if [[ -z "$role" ]]; then
      return 0
    fi
    case "$role" in
      product_manager|architect|frontend|backend|devops|ceo) break ;;
      *)
        echo "Unsupported role: $role"
        ;;
    esac
  done
  printf '%s\n' "$role"
}

resolve_input() {
  local input_file
  while true; do
    input_file="$(ask "Path to markdown input file" "input.md")"
    if [[ ! -f "$input_file" ]]; then
      echo "Input file not found: $input_file"
      continue
    fi
    if [[ "${input_file##*.}" != "md" ]]; then
      echo "Input must be a .md file: $input_file"
      continue
    fi
    printf '%s\n' "$input_file"
    return 0
  done
}

mode="$(ask "Run type (new or resume)" "new")"
case "${mode}" in
  new|resume)
    ;;
  *)
    echo "Unsupported run type: $mode"
    exit 2
    ;;
esac

use_yolo="$(ask_yes_no "Enable CEO --yolo mode? (y/n)" "n")"
while [[ "$use_yolo" == "invalid" ]]; do
  use_yolo="$(ask_yes_no "Enable CEO --yolo mode? (y/n)" "n")"
done

cmd=("$RUN_PLAYBOOK")

if [[ "$mode" == "resume" ]]; then
  target_role="$(pick_role)"
  if [[ -n "$target_role" ]]; then
    cmd+=(--role "$target_role")
  fi
  if [[ "$use_yolo" == "yes" ]]; then
    cmd+=(--yolo)
  fi
else
  run_mode="$(pick_mode)"
  input_file="$(resolve_input)"
  cmd+=(--mode "$run_mode" "$input_file")
  if [[ "$use_yolo" == "yes" ]]; then
    cmd+=(--yolo)
  fi
fi

cmd=( "${cmd[@]}" )
if [[ "$mode" == "resume" ]]; then
  cmd+=(--resume)
fi

echo
echo "Launching:"
printf '  %q' "${cmd[@]}"
echo
while true; do
  confirmed="$(ask "Continue? (y/n)" "y")"
  case "${confirmed,,}" in
    y|yes)
      break
      ;;
    n|no)
      echo "Aborted."
      exit 0
      ;;
    *)
      echo "Please answer y or n."
      ;;
  esac
done

exec "${cmd[@]}"
