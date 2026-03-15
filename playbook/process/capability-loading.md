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
- which required, conditional, and reference-only artifacts apply to the role

The load plan SHOULD include a normalized section named:

- `Resolved allowed reads by role`

These files MAY start as stubs, but they MUST NOT remain starter-placeholder
stubs once Phase 2 is handed off for implementation. A run MUST treat them as
authoritative only after the Architect replaces the placeholder content with
run-specific decisions.

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

This negative rule applies equally to UX/UI-oriented packs such as:

- uploads
- ux-measurement
- d3-custom-views
- reporting
- background-jobs
- any future advanced accessibility or analytics packs

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

## Segmentation semantics

Capability segmentation is primarily a reading, planning, copy, and activation
boundary.

It MUST be interpreted as:

- which optional contracts may be loaded
- which optional templates may be copied
- which optional integrations may be activated

It MUST NOT be interpreted as an automatic guarantee that the core runtime has
zero dormant extension points for optional features.

If a feature pack documents baseline no-op extension points in core templates,
that is still considered compliant segmentation as long as:

- the feature remains disabled in the capability profile
- the feature templates are not loaded or copied
- the feature-owned activation steps are not applied

Only a feature pack that explicitly promises full isolation MAY be treated as
having zero core-runtime footprint.

See also:

- [segmentation-model.md](segmentation-model.md)
- `../../specs/features/catalog.md`
