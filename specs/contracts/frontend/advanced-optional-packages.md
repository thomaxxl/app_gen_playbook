# Advanced Optional Frontend Packages

This file defines the cross-cutting policy for advanced optional frontend
packages.

The packages covered here are:

- `motion`
- `react-virtuoso`
- `@dnd-kit/react`
- `@xyflow/react`
- `lexical` and the approved `@lexical/*` family
- `embla-carousel-react`

These packages MUST be introduced only through capability-gated feature packs.

## Core rule

Advanced optional frontend libraries MUST NOT:

- widen the default starter dependency set
- add imports to always-loaded core runtime files
- widen the default frontend read set
- become implicit support claims without a feature pack

They MUST:

- have a catalog entry in `../../features/catalog.md`
- have a routing entry in `../../../playbook/routing/capability-map.yaml`
- ship as feature packs under `../../features/`
- ship feature-owned template entrypoints under `../../../templates/features/`
- record their exact package pins in the run-owned `runtime-bom.md`

## Segmentation rule

These advanced optional packages MUST use a `fully-isolated` segmentation model
unless a future playbook update explicitly documents a narrower exception.

That means:

- no baseline imports in core frontend runtime files
- no dormant helper imports in always-loaded code
- no package installation unless the feature is enabled

## Combination rule

Combinations of advanced optional frontend capabilities MUST NOT be assumed to
work together unless the playbook explicitly documents and validates that
combination.

Examples:

- virtualization plus drag/drop
- drag/drop plus graph canvas
- rich text plus custom markdown/html import pipelines

If a run needs one of those combinations, the run MUST record the explicit
combination decision in `runs/current/artifacts/architecture/runtime-bom.md`
and the relevant feature-owned validation artifacts.

## Baseline-alignment rule

The frontend dependency contract, the generated `package.json` template, and
the run-owned `runtime-bom.md` MUST describe the same starter toolchain.

Optional capability package pins MUST be added relative to that same baseline.

If a tracked example app or generated app drifts from the current starter
baseline, that drift MUST be treated as maintenance debt until the baseline is
deliberately repinned.
