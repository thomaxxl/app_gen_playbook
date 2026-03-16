# CEO Role Summary

Use this role only for stalled-run inspection and emergency intervention.

Its first responsibility is to gauge progress and decide whether the run is
truly blocked. If the run is blocked, the CEO MAY temporarily assume any
run-owned artifact or local `app/` responsibility needed to restore progress.
If only the operator can unblock the run, CEO must write
`runs/current/orchestrator/operator-action-required.md` and stop the requeue
loop.

Always load:

- `global-core.md`
- `process-core.md`
- `../../process/read-sets/ceo-core.md`

This role is dormant by default. It is not part of the normal phase pipeline
and SHOULD be loaded only for orchestrator-declared stall intervention or an
explicit operator request.

Full docs:

- `../../roles/ceo.md`
