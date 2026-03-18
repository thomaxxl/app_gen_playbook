# Phase I1 - Change Intake And Triage

Lead: Product Manager

## Goal

Classify the request, assign a change id, and determine whether the work is a
hotfix, an iterative change, or a full rerun.

If the request is a qualitative review that identifies defects, weaknesses, or
recommendations against the current accepted app, intake MUST treat it as a
change request that challenges the accepted baseline. It MUST NOT classify that
request as a no-op solely because the current app still matches the last
accepted baseline.

## Outputs

- a product-owned change workspace under `runs/current/changes/<change_id>/`
- packet files for `request.md`, `classification.yaml`,
  `impact-manifest.yaml`, `affected-artifacts.md`,
  `affected-app-paths.md`, and `reopened-gates.md`
- change classification
- affected-domain summary
- Architect inbox handoff
- explicit baseline-challenge note in the change packet when the request is a
  review-style critique of the accepted app
