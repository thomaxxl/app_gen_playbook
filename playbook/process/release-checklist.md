# Release Checklist

Use this checklist before treating the playbook repo as clean for publication
or broad reuse.

## Run-state hygiene

- confirm the tracked `runs/template/` tree is neutral
- confirm tracked playbook files do not contain a real domain brief
- confirm local `runs/current/` is not being relied on as tracked source

## Template hygiene

- confirm generated-app templates do not require unresolved placeholders to
  remain in `app/`
- confirm no `templates/app/**` file still contains a stale
  `<REPLACE_WITH_...>` token that is supposed to be materialized before app
  generation

## Capability hygiene

- confirm `specs/features/catalog.md` matches the actual `specs/features/`
  tree
- confirm each feature-pack README declares owner role, maturity, and
  segmentation model

## Baseline hygiene

- confirm maintained runtime decisions live in
  `playbook/process/runtime-baseline.md`
- confirm `example/` is not being used as the normative source for runtime or
  dependency decisions

## Role/read-set hygiene

- confirm role startup reads stay aligned with the `read-sets/` manifests
- confirm role docs do not silently regrow large hard-coded startup trees

## Suggested checks

```bash
rg -n "<REPLACE_WITH_" templates app
rg -n "dating site|airport|restaurant" runs/template README.md playbook specs templates
find specs/features -mindepth 1 -maxdepth 1 -type d | sort
git diff --check
```
