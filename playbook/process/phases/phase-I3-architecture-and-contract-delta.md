# Phase I3 - Architecture And Contract Delta

Lead: Architect

## Goal

Determine which contracts, capability decisions, and implementation lanes are
affected by the change.

If Product Manager marked the request as a baseline challenge or review-driven
delta, Architect MUST preserve the reopened lanes needed to resolve those
findings unless exact current evidence proves the raised issues are already
resolved. Matching the accepted baseline alone is not sufficient proof.

## Outputs

- impact analysis
- contract delta
- compatibility classification
- migration decision
- role-load manifests under `runs/current/changes/<change_id>/role-loads/`
- updated `affected-artifacts.md`, `affected-app-paths.md`, and
  `reopened-gates.md` when architecture analysis changes the delta boundary
- routed frontend/backend/devops handoffs
- no-op closure only when the current app and packet evidence explicitly answer
  the review findings, not merely when current hashes match the accepted
  baseline
