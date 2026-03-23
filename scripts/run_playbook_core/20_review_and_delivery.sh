# shellcheck shell=bash

runtime_role_from_label() {
  case "$1" in
    product_manager|product-manager) printf '%s\n' "product_manager" ;;
    architect) printf '%s\n' "architect" ;;
    frontend) printf '%s\n' "frontend" ;;
    backend) printf '%s\n' "backend" ;;
    qa) printf '%s\n' "qa" ;;
    deployment|devops) printf '%s\n' "deployment" ;;
    ceo) printf '%s\n' "ceo" ;;
    *) return 1 ;;
  esac
}

message_field() {
  local field_name="$1"
  local message_path="$2"
  local aliases=()
  case "$field_name" in
    from)
      aliases=(from sender)
      ;;
    to)
      aliases=(to receiver)
      ;;
    gate_status)
      aliases=(gate_status gate-status "gate status")
      ;;
    *)
      aliases=("$field_name")
      ;;
  esac

  awk -v targets="$(printf '%s\n' "${aliases[@]}")" '
    function norm(value, out) {
      out = tolower(value)
      gsub(/[^a-z0-9]/, "", out)
      return out
    }
    BEGIN {
      split(targets, raw_targets, "\n")
      for (i in raw_targets) {
        if (raw_targets[i] != "") {
          wanted[norm(raw_targets[i])] = 1
        }
      }
    }
    /^[[:space:]]*$/ {
      if (saw_headers) {
        exit
      }
      next
    }
    /^##[[:space:]]+/ { exit }
    {
      line = $0
      if (line ~ /^[[:space:]]*[A-Za-z][A-Za-z0-9_ -]*[[:space:]]*:/) {
        saw_headers = 1
        key = line
        sub(/:.*/, "", key)
        if (norm(key) in wanted) {
          sub(/^[^:]*:[[:space:]]*/, "", line)
          print line
          exit
        }
        next
      }
      if (saw_headers) {
        exit
      }
    }
  ' "$message_path"
}

message_gate_status() {
  local message_path="$1"
  local gate_status
  gate_status="$(awk '
    /^##[[:space:]]+Gate Status[[:space:]]*$/ { in_section=1; next }
    /^##[[:space:]]+/ { if (in_section) exit }
    in_section && /^[[:space:]]*-[[:space:]]+/ {
      sub(/^[[:space:]]*-[[:space:]]*/, "", $0)
      print $0
      exit
    }
  ' "$message_path")"
  if [[ -n "$gate_status" ]]; then
    printf '%s\n' "$gate_status"
    return 0
  fi
  message_field gate_status "$message_path"
}

message_indicates_progress() {
  local message_path="$1"
  local gate_status topic

  gate_status="$(message_gate_status "$message_path" | tr '[:upper:]' '[:lower:]')"
  case "$gate_status" in
    pass|"pass with assumptions") return 0 ;;
    blocked) return 1 ;;
  esac

  topic="$(message_field topic "$message_path" | tr '[:upper:]' '[:lower:]')"
  case "$topic" in
    acceptance-trigger-correction|acceptance-trigger-superseded|product-recovery-acknowledged)
      return 0
      ;;
  esac
  [[ "$topic" =~ (^|[-_])(complete|completed|ready|approved|resolved)$ ]]
}

orchestrator_note_has_active_owner_lane() {
  local message_path="$1"
  local sender topic

  sender="$(message_field from "$message_path" | tr '[:upper:]' '[:lower:]')"
  topic="$(message_field topic "$message_path" | tr '[:upper:]' '[:lower:]')"

  if [[ "$sender" == "architect" ]] && [[ "$topic" == "integration-review-block-persists" ]]; then
    if [[ "$(role_actionable_count frontend)" -gt 0 ]] || [[ "$(role_actionable_count backend)" -gt 0 ]]; then
      return 0
    fi
  fi

  return 1
}

browser_proof_capture_status() {
  [[ -f "$FRONTEND_BROWSER_PROOF_MD" ]] || return 1
  awk -F':[[:space:]]*' '$1 == "- capture_status" { print $2; exit }' "$FRONTEND_BROWSER_PROOF_MD"
}

host_runtime_http_admin_ready() {
  local base_url
  base_url="$(host_runtime_frontend_base_url)"
  python3 - "$base_url" <<'PY' >/dev/null 2>&1
from __future__ import annotations
import sys
import urllib.error
import urllib.request

url = sys.argv[1].rstrip("/") + "/admin/"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        status = getattr(response, "status", 0)
        body = response.read(2048).decode("utf-8", errors="ignore")
except (OSError, urllib.error.URLError):
    raise SystemExit(1)

if status < 200 or status >= 400:
    raise SystemExit(1)
if "<!doctype html" not in body.lower() and "<html" not in body.lower():
    raise SystemExit(1)
PY
}

browser_proof_fallback_ready() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  host_runtime_verification_field_ok frontend_bind || return 1
  [[ "$(browser_proof_capture_status || true)" == "environment-blocked" ]] || return 1
  host_runtime_http_admin_ready || return 1
  return 0
}

browser_proof_fallback_evidence_ready() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  host_runtime_verification_field_ok frontend_bind || return 1
  [[ "$(browser_proof_capture_status || true)" == "environment-blocked" ]] || return 1
  return 0
}

product_acceptance_pending() {
  local product_root="$STATE_ROOT/product_manager"
  [[ -d "$product_root" ]] || return 1
  find "$product_root" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | grep -q .
}

artifact_status_value() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$path"
}

browser_fallback_acceptance_signature() {
  local integration_review="$RUN_ROOT/artifacts/architecture/integration-review.md"
  local acceptance_review="$RUN_ROOT/artifacts/product/acceptance-review.md"
  local integration_status acceptance_status frontend_bind capture_status
  integration_status="$(artifact_status_value "$integration_review" || printf '%s' missing)"
  acceptance_status="$(artifact_status_value "$acceptance_review" || printf '%s' missing)"
  frontend_bind="$(host_runtime_verification_field_value frontend_bind || printf '%s' missing)"
  capture_status="$(browser_proof_capture_status || printf '%s' missing)"
  python3 - "$PLAYBOOK_RUNTIME_ENV" "$frontend_bind" "$capture_status" "$integration_status" "$acceptance_status" <<'PY'
from __future__ import annotations

import hashlib
import sys

digest = hashlib.sha256()
for value in sys.argv[1:]:
    digest.update(value.encode("utf-8"))
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

browser_fallback_acceptance_signature_recorded() {
  local signature="$1"
  [[ -f "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES" ]] || return 1
  grep -Fxq "$signature" "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES"
}

record_browser_fallback_acceptance_signature() {
  local signature="$1"
  mkdir -p "$(dirname "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES")"
  printf '%s\n' "$signature" >> "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES"
}

integration_review_allows_product_acceptance() {
  local path="$1"
  [[ -f "$path" ]] || return 1

  local integration_status
  integration_status="$(awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$path")"
  case "$integration_status" in
    ready-for-handoff|approved)
      return 0
      ;;
  esac
  return 1
}

queue_browser_fallback_product_acceptance() {
  browser_proof_fallback_evidence_ready || return 1
  product_acceptance_pending && return 1

  local integration_review="$RUN_ROOT/artifacts/architecture/integration-review.md"
  [[ -f "$integration_review" ]] || return 1
  integration_review_allows_product_acceptance "$integration_review" || return 1

  local acceptance_review="$RUN_ROOT/artifacts/product/acceptance-review.md"
  if [[ -f "$acceptance_review" ]]; then
    local acceptance_status
    acceptance_status="$(awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$acceptance_review")"
    if [[ "$acceptance_status" == "approved" ]]; then
      return 1
    fi
  fi

  local acceptance_signature
  acceptance_signature="$(browser_fallback_acceptance_signature)"
  if browser_fallback_acceptance_signature_recorded "$acceptance_signature"; then
    log "product-acceptance-browser-fallback-suppressed reason=duplicate-signature signature=$acceptance_signature"
    return 1
  fi

  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/product_manager/inbox/${stamp}-from-orchestrator-to-product_manager-integration-acceptance.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: product_manager
topic: integration-acceptance
purpose: proceed with product acceptance using the approved host-runtime fallback evidence for browser verification
change_id: ${ACTIVE_CHANGE_ID}
orchestrator_signature: ${acceptance_signature}

## Required Reads
- runs/current/artifacts/architecture/integration-review.md
- runs/current/evidence/contract-samples.md
- runs/current/evidence/frontend-usability.md
- runs/current/evidence/frontend-browser-proof.md
- runs/current/evidence/ui-previews/manifest.md
- runs/current/evidence/quality/quality-summary.md

## Requested Outputs
- review the phase-6 fallback evidence and determine final product acceptance

## Dependencies
- host runtime reached the live /admin surface and frontend browser-proof fallback was recorded

## Gate Status
- pass with assumptions

## Implementation Evidence
- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}
- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}
- runs/current/evidence/ui-previews/manifest.md

## Blocking Issues
- no architect-owned integration blockers remain open in queue

## Notes
- host runtime reached the live frontend URL, but automated browser-proof capture timed out and was recorded as the exact environment-blocked fallback allowed by phase 6
- product acceptance should judge whether the evidence pack is sufficient to pass with assumptions, mirroring the documented blocked-environment fallback path
EOF
  record_browser_fallback_acceptance_signature "$acceptance_signature"
  log "product-acceptance-queued-from-browser-fallback note=${note_path#$ROOT/}"
  append_run_remark \
    "Product Acceptance Queued From Browser Fallback" \
    "Queued Product acceptance note:\n- ${note_path#$ROOT/}\n\nEvidence:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}\n- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}"
  return 0
}

emit_ceo_escalation_note() {
  local processed_message_path="$1"
  local original_sender="$2"
  local original_topic="$3"
  local reason="$4"
  local stamp note_path relative_processed_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-escalation.md"
  relative_processed_path="${processed_message_path#$ROOT/}"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: orchestrator-escalation
purpose: inspect an orchestrator-routed blocked-run escalation and decide how the run should continue
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md
- ${relative_processed_path}

## Requested Outputs
- record the stalled-run assessment in runs/current/remarks.md
- restore progress through an explicit reroute, recovery handoff, or blocked-run decision
- direct local playbook-runtime repairs under playbook/, scripts/, or tools/
  if those files are the blocker keeping the run stalled
- runs/current/orchestrator/operator-action-required.md if only the operator
  can unblock the run

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- ${reason}

## Notes
- original sender: ${original_sender:-unknown}
- original topic: ${original_topic:-unspecified}
- the original orchestrator escalation note has been archived for reference
- every CEO unblock intervention must be recorded in runs/current/remarks.md
- if the blocker is a local playbook or runner defect, the CEO must attempt
  that repair before escalating externally
- if the remaining blocker cannot be resolved by the agents alone after local
  repair paths are exhausted, the CEO must write
  runs/current/orchestrator/operator-action-required.md instead of re-queuing
  the same unresolved blocker
EOF
  printf '%s\n' "$note_path"
}

emit_ceo_termination_review_note() {
  local reason="$1"
  local detail="$2"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-termination-review.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: termination-review
purpose: approve or reject a pending non-success playbook termination before the orchestrator exits
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md

## Requested Outputs
- record the termination review in runs/current/remarks.md
- either restore forward progress directly or emit the reroute/recovery work needed to continue
- when the blocker is an execution-environment or localhost-runtime failure,
  inspect and terminate stale playbook-started listeners or workers if that
  is the safest repair path, then rerun the prerequisite check once
- runs/current/orchestrator/operator-action-required.md if CEO approves a blocked termination
- runs/current/orchestrator/pause-requested.md if CEO approves a clean pause instead of continuing
- do not leave the run in a terminating state without an explicit CEO decision

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- ${reason}

## Notes
- orchestrator is preparing to terminate the current run non-successfully
- the CEO must approve or reject that termination before the runner exits
- if the blocker is local to the playbook runtime, CEO should repair it instead of approving termination
- terminating detail:
${detail}
EOF
  printf '%s\n' "$note_path"
}

emit_ceo_delivery_review_note() {
  local completion_detail="$1"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-delivery-review.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: delivery-review
purpose: validate the delivered app by running app/run.sh, confirm the app works, and approve or reopen delivery
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- runs/current/evidence/frontend-browser-proof.md
- runs/current/evidence/quality/quality-summary.md
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md
- app/run.sh

## Requested Outputs
- record the delivery review in runs/current/remarks.md
- run scripts/run_playbook.sh --ceo-delivery-validate
- review runs/current/evidence/ceo-delivery-validation.md
- write runs/current/orchestrator/delivery-approved.md with an explicit metadata line \`status: approved\` when delivery is validated
- if delivery validation fails, repair the blocker directly or emit the handoff needed to continue

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- the canonical completion gate now passes, but final delivery approval is still required

## Notes
- CEO must run the delivered app through app/run.sh before the playbook can terminate successfully
- the wrapper path scripts/run_playbook.sh --ceo-delivery-validate keeps runtime logs visible in the console and writes the canonical delivery-validation artifact
- if the app does not boot cleanly or the validated routes do not respond, delivery must not be approved yet
- completion detail:
${completion_detail}
EOF
  printf '%s\n' "$note_path"
}

emit_qa_delivery_review_note() {
  local completion_detail="$1"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/qa/inbox/${stamp}-from-orchestrator-to-qa-delivery-review.md"
  mkdir -p "$STATE_ROOT/qa/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: qa
topic: pre-delivery-qa-review
purpose: independently validate the delivered app before CEO final approval
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/notes.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- runs/current/artifacts/architecture/integration-review.md
- runs/current/artifacts/product/acceptance-review.md
- runs/current/evidence/contract-samples.md
- runs/current/evidence/frontend-usability.md
- runs/current/evidence/ui-previews/manifest.md
- runs/current/evidence/quality/review-plan.json
- runs/current/evidence/quality/ui-copy-audit.md
- runs/current/evidence/quality/test-results.md
- runs/current/evidence/quality/quality-summary.md
- playbook/task-bundles/qa-delivery-review.yaml
- playbook/roles/qa.md
- app/run.sh

## Requested Outputs
- run \`cd app/frontend && npm run capture:qa-screenshots\` to save screenshots for every required review-plan surface
- record the QA review in runs/current/evidence/qa-delivery-review.md
- make sure runs/current/evidence/ui-previews/qa-manifest.md exists and cites the captured screenshot files
- run app/run.sh and confirm the delivered app boots
- perform basic live user testing against the app
- reject delivery if the frontend is blank, visibly crashed, flickering from obvious request loops, or still exposing metadata/debug/recovery copy
- reject delivery if backend runtime errors appear during the tested flows
- if QA fails, create the owner handoffs needed to reopen the run
- if QA passes, mark runs/current/evidence/qa-delivery-review.md with explicit approval fields

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- the canonical completion gate passed, but independent QA validation is still required before CEO delivery approval

## Notes
- QA is a pre-delivery validation lane only; it should not silently patch the app
- the QA decision must be based on live behavior, not only on prior evidence claims
- final QA approval is incomplete without the review-plan screenshot set under runs/current/evidence/ui-previews/qa/
- completion detail:
${completion_detail}
EOF
  printf '%s\n' "$note_path"
}

qa_delivery_review_approved() {
  "$PLAYBOOK_PYTHON" "$ROOT/tools/check_delivery_gate_status.py" --repo-root "$ROOT" --qa-terminal >/dev/null
}

delivery_approved() {
  "$PLAYBOOK_PYTHON" "$ROOT/tools/check_delivery_gate_status.py" --repo-root "$ROOT" --delivery-recorded >/dev/null
}

process_orchestrator_inbox() {
  local orchestrator_dir="$STATE_ROOT/orchestrator"
  local inbox_dir="$orchestrator_dir/inbox"
  local processed_dir="$orchestrator_dir/processed"
  local oldest processed_path sender topic ceo_note reason

  [[ -d "$inbox_dir" ]] || return 1
  oldest="$(find "$inbox_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
  if [[ -z "$oldest" ]]; then
    return 1
  fi

  mkdir -p "$processed_dir"
  processed_path="$processed_dir/$(basename "$oldest")"
  mv "$oldest" "$processed_path"

  sender="$(message_field from "$processed_path")"
  topic="$(message_field topic "$processed_path")"
  if [[ "$sender" == "ceo" ]]; then
    log "orchestrator-note-archived-without-reescalation message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Note Archived Without CEO Re-escalation" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- CEO-originated reroute notes must not be escalated back to CEO."
    append_run_remark \
      "Orchestrator Note Archived Without CEO Re-escalation" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- CEO-originated reroute notes now return control to normal dispatch instead of looping back into CEO."
    return 0
  fi
  if message_indicates_progress "$processed_path"; then
    log "orchestrator-progress-note-archived message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Progress Note Archived" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- Success-path progress notes do not require CEO triage and should return control to normal recovery or dispatch."
    append_run_remark \
      "Orchestrator Progress Note Archived" \
      "Archived orchestrator progress note:\n- ${processed_path#$ROOT/}\n\nReason:\n- Success-path progress notes do not require CEO triage and should return control to normal recovery or dispatch."
    return 0
  fi
  if orchestrator_note_has_active_owner_lane "$processed_path"; then
    log "orchestrator-blocked-note-archived-active-owner message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Blocked Note Archived With Active Owner Lane" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- The note is blocked, but the run already has active normal-owner work in flight so CEO triage would only create a false stall."
    append_run_remark \
      "Orchestrator Blocked Note Archived With Active Owner Lane" \
      "Archived orchestrator blocked note:\n- ${processed_path#$ROOT/}\n\nReason:\n- The note is blocked, but Frontend or Backend already has actionable work so the runner should continue normal dispatch instead of re-escalating to CEO."
    return 0
  fi
  reason="orchestrator-routed escalation requires CEO triage: ${processed_path#$ROOT/}"
  ceo_note="$(emit_ceo_escalation_note "$processed_path" "$sender" "$topic" "$reason")"

  log "orchestrator-escalated message=$(basename "$processed_path") ceo_note=$ceo_note"
  append_recovery_log \
    "Orchestrator Escalation Routed To CEO" \
    "Original note:\n- ${processed_path#$ROOT/}\n\nCEO note:\n- ${ceo_note#$ROOT/}"
  append_run_remark \
    "Orchestrator Escalation Routed To CEO" \
    "Archived orchestrator escalation:\n- ${processed_path#$ROOT/}\n\nQueued CEO intervention:\n- ${ceo_note#$ROOT/}"
  return 0
}

