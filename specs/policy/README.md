# Policy Registry

This directory is the executable sidecar policy layer for the playbook.

Use it when a human-readable contract in `playbook/` or `specs/` must become a
machine-resolved requirement instead of remaining prose-only.

## Layout

- `schema/`: JSON Schemas for requirement sets, profiles, and waivers
- `requirements/`: machine-readable requirement sets grouped by contract family
- `profiles/`: composable active-policy subsets for roles, phases, gates, and
  run modes
- `compiled/`: generated policy registry output

## Rule

Human-readable Markdown remains the source of intent.

The executable source of enforcement is the sidecar policy entry that names:

- a stable requirement ID
- the owner/family/class
- the active profiles
- the validator entrypoint
- the evidence/remediation model

A new `MUST`/`MUST NOT` clause is incomplete until it has a requirement ID and
an enforcement path here.

## Commands

```bash
python3 tools/contracts/compile_requirements.py
python3 tools/contracts/resolve_active_policy.py --role product_manager --phase phase-7-product-acceptance --gate acceptance
python3 tools/contracts/evaluate_policy.py --profile process-core
```
