# shellcheck shell=bash

pending_actionable_count() {
  local requested_lane="${1:-}"
  local count=0
  local role_dir lane path

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    for lane in inbox inflight; do
      if [[ -n "$requested_lane" && "$lane" != "$requested_lane" ]]; then
        continue
      fi
      for path in "$role_dir/$lane"/*.md; do
        [[ -f "$path" ]] || continue
        count=$((count + 1))
      done
    done
  done < <(canonical_queue_dirs)

  printf '%s\n' "$count"
}

actionable_owner_queue_fingerprint() {
  python3 - "$STATE_ROOT" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

state_root = Path(sys.argv[1])
role_names = ["product_manager", "architect", "frontend", "backend", "qa"]
if (state_root / "devops").is_dir():
    role_names.append("devops")
elif (state_root / "deployment").is_dir():
    role_names.append("deployment")

digest = hashlib.sha256()
for role_name in role_names:
    role_dir = state_root / role_name
    for lane in ("inbox", "inflight"):
        lane_dir = role_dir / lane
        if not lane_dir.is_dir():
            continue
        for path in sorted(lane_dir.glob("*.md")):
            rel = path.relative_to(state_root)
            digest.update(str(rel).encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")

print(digest.hexdigest())
PY
}

extract_json_string_field() {
  local json_file="$1"
  local field_name="$2"
  python3 - "$json_file" "$field_name" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = payload.get(sys.argv[2], "")
if isinstance(value, str):
    print(value)
else:
    print("")
PY
}

format_handoff_validation_blockers() {
  local json_file="$1"
  python3 - "$json_file" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
blockers = payload.get("blockers", [])
for blocker in blockers:
    if isinstance(blocker, dict):
        print(f"- {blocker.get('message', '')}")
PY
}

archive_duplicate_queue_trace() {
  local runtime_role="$1"
  local duplicate_path="$2"
  local processed_dir="$3"
  local source_lane="$4"
  local stamp base archived_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$duplicate_path" .md)"
  archived_path="$processed_dir/${base}.duplicate-${source_lane}-${stamp}.md"
  mv "$duplicate_path" "$archived_path"
  log "queue-duplicate-archived role=$runtime_role source=$source_lane archived=${archived_path#$ROOT/}"
}

archive_stale_correction_queue_traces() {
  local changed=1
  local source_path archived_path replacement_path

  while IFS=$'\t' read -r source_path archived_path replacement_path; do
    [[ -n "$source_path" ]] || continue
    log "queue-stale-correction-archived source=$source_path archived=$archived_path replacement=$replacement_path"
    changed=0
  done < <(python3 "$ROOT/tools/archive_stale_correction_notes.py" --repo-root "$ROOT")

  return "$changed"
}

archive_legacy_deployment_duplicate() {
  local duplicate_path="$1"
  local lane="$2"
  local processed_dir="$STATE_ROOT/deployment/processed"
  local stamp base archived_path

  mkdir -p "$processed_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$duplicate_path" .md)"
  archived_path="$processed_dir/${base}.legacy-duplicate-${lane}-${stamp}.md"
  mv "$duplicate_path" "$archived_path"
  log "queue-legacy-deployment-duplicate archived=${archived_path#$ROOT/}"
}

migrate_legacy_deployment_queue() {
  local changed=1
  local lane path basename target

  if [[ ! -d "$STATE_ROOT/devops" || ! -d "$STATE_ROOT/deployment" ]]; then
    return 1
  fi

  mkdir -p "$STATE_ROOT/devops/inbox" "$STATE_ROOT/devops/inflight" "$STATE_ROOT/deployment/processed"

  for lane in inbox inflight; do
    for path in "$STATE_ROOT/deployment/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      basename="$(basename "$path")"
      if [[ -f "$STATE_ROOT/devops/inbox/$basename" || -f "$STATE_ROOT/devops/inflight/$basename" || -f "$STATE_ROOT/devops/processed/$basename" ]]; then
        archive_legacy_deployment_duplicate "$path" "$lane"
      else
        target="$STATE_ROOT/devops/$lane/$basename"
        mv "$path" "$target"
        log "queue-legacy-deployment-migrated source=${path#$ROOT/} target=${target#$ROOT/}"
      fi
      changed=0
    done
  done

  return "$changed"
}

is_canonical_queue_path() {
  local path="$1"
  local rel
  rel="${path#$STATE_ROOT/}"

  case "$rel" in
    product_manager/inbox/*.md|product_manager/inflight/*.md|\
    architect/inbox/*.md|architect/inflight/*.md|\
    frontend/inbox/*.md|frontend/inflight/*.md|\
    backend/inbox/*.md|backend/inflight/*.md|\
    qa/inbox/*.md|qa/inflight/*.md|\
    ceo/inbox/*.md|ceo/inflight/*.md)
      return 0
      ;;
    orchestrator/inbox/*.md|orchestrator/inflight/*.md)
      [[ -d "$STATE_ROOT/orchestrator" ]] && return 0
      ;;
    devops/inbox/*.md|devops/inflight/*.md)
      [[ -d "$STATE_ROOT/devops" ]] && return 0
      ;;
    deployment/inbox/*.md|deployment/inflight/*.md)
      [[ ! -d "$STATE_ROOT/devops" ]] && [[ -d "$STATE_ROOT/deployment" ]] && return 0
      ;;
  esac
  return 1
}

quarantine_noncanonical_queue_traces() {
  local changed=1
  local quarantine_root="$EVIDENCE_ROOT/quarantine/queue"
  local path rel archived_path

  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    if is_canonical_queue_path "$path"; then
      continue
    fi
    rel="${path#$STATE_ROOT/}"
    archived_path="$quarantine_root/$rel"
    mkdir -p "$(dirname "$archived_path")"
    mv "$path" "$archived_path"
    log "queue-invalid-archived source=${path#$ROOT/} archived=${archived_path#$ROOT/}"
    changed=0
  done < <(find "$STATE_ROOT" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f 2>/dev/null | sort)

  return "$changed"
}

normalize_queue_state() {
  local changed=1

  if migrate_legacy_deployment_queue; then
    changed=0
  fi

  if quarantine_noncanonical_queue_traces; then
    changed=0
  fi

  if archive_stale_correction_queue_traces; then
    changed=0
  fi

  return "$changed"
}

oldest_role_queue_file() {
  local lane="$1"
  shift
  local role_dir path
  for role_dir in "$@"; do
    for path in "$role_dir/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      printf '%s::%s\n' "$role_dir" "$path"
    done
  done | sort -t: -k3,3 | head -n 1
}

oldest_operator_queue_file() {
  local lane="$1"
  shift
  local role_dir path
  for role_dir in "$@"; do
    for path in "$role_dir/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      if grep -Eqi '^(from|sender):[[:space:]]*operator[[:space:]]*$' "$path"; then
        printf '%s::%s\n' "$role_dir" "$path"
      fi
    done
  done | sort -t: -k3,3 | head -n 1
}

message_supersedes_basename() {
  local message_path="$1"
  local supersedes
  supersedes="$(message_field supersedes "$message_path" | tr -d '\r')"
  if [[ -z "$supersedes" ]]; then
    return 1
  fi
  basename "$supersedes"
}

archive_superseded_queue_trace() {
  local runtime_role="$1"
  local superseded_path="$2"
  local processed_dir="$3"
  local source_lane="$4"
  local superseding_path="$5"
  local stamp base superseding_base archived_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$superseded_path" .md)"
  superseding_base="$(basename "$superseding_path" .md)"
  archived_path="$processed_dir/${base}.superseded-by-${superseding_base}-${source_lane}-${stamp}.md"
  mv "$superseded_path" "$archived_path"
  log "queue-superseded-archived role=$runtime_role source=$source_lane archived=${archived_path#$ROOT/} superseding=$(basename "$superseding_path")"
}

archive_superseded_messages_for_dirs() {
  local runtime_role="$1"
  shift
  local candidate_dirs=("$@")
  local changed=1
  local role_dir path processed_dir supersedes lane target_path target_role_dir

  for role_dir in "${candidate_dirs[@]}"; do
    mkdir -p "$role_dir/processed"
  done

  for role_dir in "${candidate_dirs[@]}"; do
    for path in "$role_dir/inflight"/*.md "$role_dir/inbox"/*.md; do
      [[ -f "$path" ]] || continue
      supersedes="$(message_supersedes_basename "$path" || true)"
      [[ -n "$supersedes" ]] || continue
      target_role_dir=""
      for target_role_dir in "${candidate_dirs[@]}"; do
        for lane in inflight inbox; do
          target_path="$target_role_dir/$lane/$supersedes"
          [[ -f "$target_path" ]] || continue
          [[ "$target_path" == "$path" ]] && continue
          processed_dir="$target_role_dir/processed"
          mkdir -p "$processed_dir"
          archive_superseded_queue_trace "$runtime_role" "$target_path" "$processed_dir" "$lane" "$path"
          changed=0
        done
      done
    done
  done

  return "$changed"
}

pending_operator_priority_role() {
  local role_dir role_name runtime_role
  local operator_line path best_role="" best_name=""

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    role_name="$(basename "$role_dir")"
    [[ "$role_name" == "orchestrator" ]] && continue
    runtime_role="$(runtime_role_from_label "$role_name" 2>/dev/null || true)"
    [[ -n "$runtime_role" ]] || continue

    for operator_line in \
      "$(oldest_operator_queue_file inflight "$role_dir")" \
      "$(oldest_operator_queue_file inbox "$role_dir")"; do
      [[ -n "$operator_line" ]] || continue
      path="${operator_line#*::}"
      if [[ -z "$best_name" || "$(basename "$path")" < "$best_name" ]]; then
        best_name="$(basename "$path")"
        best_role="$runtime_role"
      fi
    done
  done < <(canonical_queue_dirs)

  [[ -n "$best_role" ]] || return 1
  printf '%s\n' "$best_role"
}

pending_inflight_role() {
  local role_dir role_name runtime_role
  local queue_line path best_role="" best_name=""

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    role_name="$(basename "$role_dir")"
    [[ "$role_name" == "orchestrator" ]] && continue
    runtime_role="$(runtime_role_from_label "$role_name" 2>/dev/null || true)"
    [[ -n "$runtime_role" ]] || continue

    queue_line="$(oldest_role_queue_file inflight "$role_dir")"
    [[ -n "$queue_line" ]] || continue
    path="${queue_line#*::}"
    if [[ -z "$best_name" || "$(basename "$path")" < "$best_name" ]]; then
      best_name="$(basename "$path")"
      best_role="$runtime_role"
    fi
  done < <(canonical_queue_dirs)

  [[ -n "$best_role" ]] || return 1
  printf '%s\n' "$best_role"
}

pause_drain_in_progress() {
  [[ "$(pending_actionable_count inflight)" -gt 0 ]] && return 0
  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    return 0
  fi
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    return 0
  fi
  return 1
}

steering_request_blocks_new_claims() {
  [[ -f "$KILL_REQUESTED_MD" ]] && return 0
  [[ -f "$PAUSE_REQUESTED_MD" ]] && return 0
  return 1
}

newer_pending_operator_override_path() {
  local role_dir path newest=""

  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    [[ "$(basename "$role_dir")" == "orchestrator" ]] && continue
    for path in "$role_dir/inflight"/*.md "$role_dir/inbox"/*.md; do
      [[ -f "$path" ]] || continue
      if ! grep -Eqi '^(from|sender):[[:space:]]*operator[[:space:]]*$' "$path"; then
        continue
      fi
      if [[ "$path" -nt "$OPERATOR_ACTION_REQUIRED_MD" ]] && [[ -z "$newest" || "$path" -nt "$newest" ]]; then
        newest="$path"
      fi
    done
  done < <(canonical_queue_dirs)

  [[ -n "$newest" ]] || return 1
  printf '%s\n' "$newest"
}

clear_superseded_operator_action_required() {
  local override_path archive_dir archived_path stamp

  override_path="$(newer_pending_operator_override_path || true)"
  [[ -n "$override_path" ]] || return 1

  archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-archived override=$(basename "$override_path") archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Operator Override Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nNewer operator note:\n- ${override_path#$ROOT/}"
  append_run_remark \
    "Operator Override Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nNewer operator note:\n- ${override_path#$ROOT/}"
  return 0
}

claim_message() {
  local runtime_role="$1"
  local candidate_dirs=()
  case "$runtime_role" in
    deployment)
      if [[ -d "$STATE_ROOT/devops" ]]; then
        candidate_dirs+=("$STATE_ROOT/devops")
      fi
      if [[ -d "$STATE_ROOT/deployment" ]]; then
        candidate_dirs+=("$STATE_ROOT/deployment")
      fi
      if [[ "${#candidate_dirs[@]}" -eq 0 ]]; then
        candidate_dirs+=("$STATE_ROOT/devops" "$STATE_ROOT/deployment")
      fi
      ;;
    *)
      candidate_dirs+=("$(role_state_dir "$runtime_role")")
      ;;
  esac

  local role_dir inflight_dir inbox_dir processed_dir
  for role_dir in "${candidate_dirs[@]}"; do
    mkdir -p "$role_dir/inflight" "$role_dir/inbox" "$role_dir/processed"
  done

  local existing oldest claimed basename source_role_dir operator_priority_line
  while true; do
    if [[ -f "$KILL_REQUESTED_MD" ]]; then
      return 1
    fi

    archive_superseded_messages_for_dirs "$runtime_role" "${candidate_dirs[@]}" || true

    existing=""
    source_role_dir=""
    operator_priority_line="$(oldest_operator_queue_file inflight "${candidate_dirs[@]}")"
    if [[ -n "$operator_priority_line" ]]; then
      source_role_dir="${operator_priority_line%%::*}"
      existing="${operator_priority_line#*::}"
    fi
    while [[ -z "$existing" ]] && IFS= read -r line; do
      source_role_dir="${line%%::*}"
      existing="${line#*::}"
      break
    done < <(oldest_role_queue_file inflight "${candidate_dirs[@]}")
    if [[ -n "$existing" ]]; then
      inflight_dir="$source_role_dir/inflight"
      processed_dir="$source_role_dir/processed"
      basename="$(basename "$existing")"
      if [[ -f "$processed_dir/$basename" ]]; then
        archive_duplicate_queue_trace "$runtime_role" "$existing" "$processed_dir" "inflight"
        continue
      fi
      printf '%s\n' "$existing"
      return 0
    fi

    if steering_request_blocks_new_claims; then
      return 1
    fi

    oldest=""
    source_role_dir=""
    operator_priority_line="$(oldest_operator_queue_file inbox "${candidate_dirs[@]}")"
    if [[ -n "$operator_priority_line" ]]; then
      source_role_dir="${operator_priority_line%%::*}"
      oldest="${operator_priority_line#*::}"
    fi
    while [[ -z "$oldest" ]] && IFS= read -r line; do
      source_role_dir="${line%%::*}"
      oldest="${line#*::}"
      break
    done < <(oldest_role_queue_file inbox "${candidate_dirs[@]}")
    if [[ -z "$oldest" ]]; then
      return 1
    fi

    inbox_dir="$source_role_dir/inbox"
    inflight_dir="$source_role_dir/inflight"
    processed_dir="$source_role_dir/processed"
    basename="$(basename "$oldest")"
    if [[ -f "$processed_dir/$basename" || -f "$inflight_dir/$basename" ]]; then
      archive_duplicate_queue_trace "$runtime_role" "$oldest" "$processed_dir" "inbox"
      continue
    fi

    claimed="$inflight_dir/$basename"
    mv "$oldest" "$claimed"
    printf '%s\n' "$claimed"
    return 0
  done
}

