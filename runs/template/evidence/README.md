# Evidence Template Root

Use local `runs/current/evidence/` for real verification evidence.

The tracked template remains intentionally empty except for this starter note.

Expected run-owned evidence includes, when applicable:

- `contract-samples.md`
- `frontend-usability.md` describing the reviewed entry/custom/generated pages
  and whether any internal debug or recovery copy leaked into visible UI
- `quality/` containing:
  - `crud-matrix.md`
  - `seed-data-audit.md`
  - `ui-copy-audit.md`
  - `test-results.md`
  - `quality-summary.md`
- `ui-previews/*.png` or similar Playwright-captured preview screenshots for
  materially changed UI flows
- orchestrator JSONL turn logs under `evidence/orchestrator/jsonl/`
- `evidence/orchestrator/recovery-log.md` for synthesized recovery notes,
  rejected handoffs, and stalled-run interventions
