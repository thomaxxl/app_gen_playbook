# Policy Registry

This directory is the executable sidecar policy layer for the playbook.

Use it when a human-readable contract in `playbook/` or `specs/` must become a
machine-resolved requirement instead of remaining prose-only.

## Layout

- `schema/`: JSON Schemas for requirement sets, profiles, and waivers
- `validators/`: registry-driven validator adapter metadata
- `requirements/`: machine-readable requirement sets grouped by contract family
- `profiles/`: composable active-policy subsets for roles, phases, gates, and
  run modes
- `sdlc/`: YAML lifecycle catalogs for lanes, phases, and overlays
- `compiled/`: generated policy registry output

## Rule

Human-readable Markdown remains the source of intent.

The executable source of enforcement is the sidecar policy entry that names:

- a stable requirement ID
- the owner/family/class
- the active profiles that explicitly activate the requirement
- the validator entrypoint
- the evidence/remediation model

A new `MUST`/`MUST NOT` clause is incomplete until it has a requirement ID and
an enforcement path here.

## Commands

```bash
python3 tools/contracts/compile_requirements.py
python3 tools/contracts/resolve_active_policy.py --role product_manager --phase phase-7-product-acceptance --gate acceptance
python3 tools/contracts/evaluate_policy.py --profile process-core
python3 tools/contracts/compile_run_facts.py
python3 tools/contracts/compile_sdlc_registry.py
python3 tools/contracts/resolve_sdlc_plan.py --run-mode new-full-run
python3 tools/contracts/evaluate_sdlc.py --run-mode new-full-run
python3 tools/contracts/check_phase_transition.py --run-mode new-full-run --from phase-6-integration-review --to phase-7-product-acceptance
python3 tools/contracts/record_attestation.py --file runs/current/policy/attestations/ATT-example.yaml
python3 tools/contracts/render_sdlc_board.py
```

## Current framework direction

- Profiles are the activation surface. Requirements do not self-activate.
- Validator dispatch is registry-driven through `validators/registry.yaml`.
- Coverage validators may still derive facts from Markdown, but the preferred
  machine-readable outputs now live under `runs/current/facts/`.
- The SDLC layer is separate from the requirement layer:
  - requirements say what must be true
  - SDLC steps say what lifecycle work must happen
  - milestones govern phase transitions
  - overlays add optional step packs, such as security
  - run-owned `runs/current/policy/extensions/*.yaml` files may add additive
    runtime steps without weakening the base lifecycle
