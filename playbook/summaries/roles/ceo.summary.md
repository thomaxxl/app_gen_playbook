# CEO Role Summary

Use this role only for stalled-run inspection, operator-requested steering,
and emergency intervention.

Its first responsibility is to gauge progress and decide whether the run is
truly blocked. If the run is blocked, the CEO MAY temporarily assume any
run-owned artifact, local `app/` responsibility, or local playbook-runtime
surface under `playbook/`, `scripts/`, or `tools/` needed to restore
progress.
If the blocker is a local playbook or orchestrator defect, CEO MUST attempt
that repair before escalating externally.
If only the operator can unblock the run after those local repair paths are
exhausted, CEO must write
`runs/current/orchestrator/operator-action-required.md` and stop the requeue
loop.
If the operator wants to pause and resume later, CEO must write
`runs/current/orchestrator/pause-requested.md` so the runner exits cleanly and
the next `scripts/run_playbook.sh --resume` can continue.
Before the orchestrator exits non-successfully, CEO must approve that
termination by either restoring progress, writing
`runs/current/orchestrator/operator-action-required.md`, or writing
`runs/current/orchestrator/pause-requested.md`.
Before successful delivery, CEO must run `scripts/run_playbook.sh --ceo-delivery-validate`,
validate `app/run.sh` booted the app successfully, and write
`runs/current/orchestrator/delivery-approved.md`.
Every CEO unblock intervention MUST be recorded in `runs/current/remarks.md`.

Always load:

- `global-core.md`
- `process-core.md`
- `../../process/read-sets/ceo-core.md`

This role is dormant by default. It is not part of the normal phase pipeline
and SHOULD be loaded only for orchestrator-declared stall intervention or an
explicit operator request.

Full docs:

- `../../roles/ceo.md`
