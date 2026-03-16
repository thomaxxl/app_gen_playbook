# Phase I0 - Baseline Alignment

Lead: Architect with affected implementation roles

## Goal

Verify that the current accepted artifacts still match the actual `app/`
implementation before a change run proceeds.

## When required

Run baseline alignment when:

- `app/` was changed outside a normal authoritative run
- `app/` was modified by app-only maintenance
- accepted artifacts are stale or disputed
- the orchestrator cannot prove the current app matches the artifact set

## Outputs

- updated current-state artifacts where drift is confirmed
- baseline evidence under `runs/current/evidence/baseline/`
- a short note in `runs/current/remarks.md`
- restored `runs/current/artifacts/**` from
  `app/docs/playbook-baseline/current/` when the portable baseline is the only
  trustworthy accepted snapshot
