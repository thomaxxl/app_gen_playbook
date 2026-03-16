# Architect Core Read Set

Compatibility wrapper only.

New task bundles MUST choose the stage-specific Architect read set instead of
using this file directly:

- `architect-authoring-core.md` for Phase 2 and change-impact authoring work
- `architect-review-core.md` for Phase 6 integration review

If a legacy task still cites `architect-core.md`, load only the one
stage-specific manifest that matches the current task. Do not preload both
unless the inbox item explicitly spans both authoring and review work.
