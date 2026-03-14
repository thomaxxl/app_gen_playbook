# Capability Loading

This file defines how optional feature packs are enabled, loaded, and
explicitly excluded.

## Core rule

Every run MUST separate:

- core contracts and templates
- optional capability packs

Core modules live under:

- `../../specs/contracts/`
- `../../templates/app/`

Optional capability packs live under:

- `../../specs/features/`
- `../../templates/features/`

## Run-owned gating artifacts

Every run MUST maintain these architecture artifacts:

- `../../runs/current/artifacts/architecture/capability-profile.md`
- `../../runs/current/artifacts/architecture/load-plan.md`

The capability profile is the authoritative enable/disable decision record.

The load plan is the shortest role-specific statement of:

- what each role MUST read
- what each role MUST NOT read

## Positive loading rule

After loading role/process core docs and the role's owned core contract
README(s), the agent MUST load only the capability packs marked `enabled` in:

- `../../runs/current/artifacts/architecture/capability-profile.md`

and listed for that role in:

- `../../runs/current/artifacts/architecture/load-plan.md`

## Negative loading rule

Disabled optional capability modules MUST NOT be:

- loaded
- summarized
- copied into the app
- used as design input
- treated as fallback implementation ideas

Undecided capability modules MUST also remain unloaded until the capability
profile explicitly enables them.

## Supporting-contract rule

Some lower-level technical directories may exist to support feature packs.

Example:

- `../../specs/contracts/files/`

These support contracts MUST be loaded only through the feature pack that owns
them, unless the task explicitly says otherwise.

## Template rule

Core templates MUST be copied from:

- `../../templates/app/`

Feature templates MUST be copied only from the enabled feature-pack entrypoint
under:

- `../../templates/features/`

The operator MUST NOT scan all optional template trees "just in case".
