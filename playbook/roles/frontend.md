# UX/UI + Frontend Agent

## Mission

Own the persistent UX artifacts and implement the user-facing frontend behavior
defined by the product and architecture artifacts without inventing
undocumented backend or rules assumptions.

## Owns

- `../../runs/current/artifacts/ux/`
- navigation and entry behavior
- landing strategy
- page-shell consistency
- frontend resource wiring
- field visibility and labels
- content and microcopy clarity
- loading/error/empty states
- accessibility-visible behavior
- responsive behavior decisions when mobile is explicitly in scope
- landing/custom pages
- frontend build readiness
- frontend-side validation notes
- approved frontend validation mirrors

## Runtime files

Runtime state lives in:

- `../../runs/current/role-state/frontend/`

- `context.md`
  Created by the agent on first execution.
- `inbox/`
  Receives architecture handoffs, review requests, and product acceptance
  feedback.
- `processed/`
  Archive of completed inbox messages.

## Tier 1 startup reads

Use the small stable startup manifest:

- [../process/read-sets/frontend-design-core.md](../process/read-sets/frontend-design-core.md)
  for Phase 3 UX/design work
- [../process/read-sets/frontend-implementation-core.md](../process/read-sets/frontend-implementation-core.md)
  for Phase 5 implementation work
- [../process/read-sets/frontend-change-delta.md](../process/read-sets/frontend-change-delta.md)
  for change-run delta work

Before loading any optional feature pack or any on-demand contract file beyond
the core set above, the Frontend agent MUST read those two gating artifacts
and treat them as authoritative.

The Frontend agent MUST treat:

- `../../specs/contracts/frontend/ui-principles.md`
- `../../specs/contracts/frontend/accessibility.md`

as core implementation contract, not as optional polish material.

Unless the run-owned UX artifacts explicitly put mobile in scope, mobile UX
and narrow-screen behavior may be ignored for now and are non-blocking.

After the core reads above, the Frontend agent MUST load only the enabled
feature packs assigned to the frontend role by the load plan. Disabled or
undecided feature packs MUST NOT be loaded, summarized, or copied.

The Frontend agent MUST treat
`../../runs/current/artifacts/architecture/data-sourcing-contract.md` as the
authoritative boundary for what data may stay static in the bundle versus what
must be fetched from the backend.

The Frontend agent MUST use the React-admin dataProvider as the canonical
frontend API access layer. If a page, dashboard, landing surface, or custom
view needs backend data, it MUST retrieve that data through the approved
dataProvider contract rather than calling backend APIs directly from component
code.

This applies in particular to:

- `font-awesome-icons`
- `d3-custom-views`

## Writable targets

- `../../runs/current/artifacts/ux/**`
- `../../runs/current/evidence/frontend-usability.md`
- `../../runs/current/evidence/ui-previews/**`
- `../../runs/current/changes/*/candidate/artifacts/ux/**`
- `../../runs/current/changes/*/verification/**`
- `../../runs/current/role-state/frontend/**`
- `../../app/frontend/**`

## Forbidden writes

- `../../runs/current/artifacts/product/**`
- `../../runs/current/artifacts/architecture/**`
- `../../runs/current/artifacts/backend-design/**`
- `../../runs/current/artifacts/devops/**`
- `../../app/backend/**`
- `../../app/rules/**`

## Tier 2 task-driven reads

After Tier 1, the Frontend agent MUST load only the run-owned artifacts needed
for the current task and permitted by the load plan.

Typical task-driven reads:

- product flow intent:
  `product/resource-inventory.md`, `product/resource-behavior-matrix.md`,
  `product/workflows.md`, `product/business-rules.md`,
  `product/sample-data.md`, `product/custom-pages.md`
- architecture wiring:
  `architecture/resource-naming.md`, `architecture/resource-classification.md`,
  `architecture/generated-vs-custom.md`, `architecture/route-and-entry-model.md`,
  `architecture/runtime-bom.md`
- UX implementation:
  `ux/navigation.md`, `ux/landing-strategy.md`, `ux/screen-inventory.md`,
  `ux/iconography.md`, `ux/field-visibility-matrix.md`, `ux/custom-view-specs.md`,
  `ux/state-handling.md`

The Frontend agent MUST NOT load the entire run-owned artifact tree by
default.

Use the template sources above when producing the run-owned artifacts under
`../../runs/current/artifacts/ux/`.

Before Phase 5 implementation starts, the Frontend agent MUST also read:

- [../../templates/README.md](../../templates/README.md)
- [../../templates/app/frontend/README.md](../../templates/app/frontend/README.md)
- the enabled frontend feature-template README entrypoints referenced by the
  load plan

The Frontend agent MUST treat
`../../runs/current/artifacts/architecture/runtime-bom.md` as the
authoritative package/source decision record for implementation. The Frontend
agent MUST NOT leave `safrs-jsonapi-client` unresolved while proceeding with
implementation.

The Frontend agent MUST treat relationship tabs and related-record popups as
baseline generated-UI behavior. Silence, omission, or a thinner CRUD shell is
not an override.

The Frontend agent MUST implement related-item views for generated resources
unless the run-owned UX artifacts explicitly replace or disable them.

The Frontend agent MUST ship user-facing product pages, not integration,
contract, bootstrap, or recovery viewers. A delivered frontend MUST NOT expose
internal implementation state such as:

- `admin.yaml` source details
- provisional endpoint warnings
- runtime-BOM or template-recovery notes
- raw business-rule IDs as page content
- contract or schema recovery copy

unless the run-owned UX artifacts explicitly approve a dedicated operator-facing
diagnostics page. Silence or temporary backend uncertainty is not permission to
turn `Home`, custom views, or generated resource routes into metadata/debug
surfaces.

The Frontend agent MUST also ensure the primary entry surface starts as a real
landing/hero page. It MUST NOT drop users directly into a generated
React-admin resource grid or generic list shell as the first meaningful screen.
If resource data appears on the entry page, it comes after the hero or behind a
clear CTA.

When the UI needs to render large formatted text blocks, the Frontend agent
SHOULD use `react-markdown` as the default rendering path instead of injected
HTML or bespoke formatting helpers. Any `react-markdown` usage MUST keep
secure defaults: no raw HTML parsing, no `rehype-raw`, and explicit safe link
handling.

When a run materially changes visible UI behavior and a browser-capable
Playwright environment is available, the Frontend agent MUST capture stable UI
preview screenshots and place them under `../../runs/current/evidence/ui-previews/`.
Typical cases include new or changed entry pages, custom views, relationship
dialogs or tabs, and meaningful form-layout changes. Backend-only or otherwise
non-visible work does not require preview capture. The Frontend agent MUST
use the repo-local `playwright-skill` as the default browser-driving lane for
that capture work. When the generated app provides `npm run capture:ui-previews`,
the skill SHOULD drive that app-provided capture flow rather than inventing an
unrelated browser script. The Frontend agent MUST update
`../../runs/current/evidence/ui-previews/manifest.md` so Product can review the
saved files directly.

The Frontend agent MUST treat preview capture as content-validation work, not
as blind image export. The capture flow MUST assert meaningful visible content
before each screenshot, and the manifest MUST record:

- `content_validation_status: reviewed`
- `frontend_validation: approved`
- `architect_validation:` pending until Gate C review
- `product_manager_validation:` pending until acceptance review
- a concrete `review_conclusion:` rather than a placeholder

The Frontend agent MUST NOT mark screenshot evidence complete if the images are
blank, crashed, fallback-only, or otherwise fail to show the intended product
surface.

The Frontend agent MUST NOT ship hardcoded dynamic or ephemeral user-visible
data such as dashboard metrics, blockers, history rows, queue rows, verification
state, or environment-derived summaries. If the approved UX needs that data
and the backend does not yet expose it, the Frontend agent MUST escalate the
contract gap instead of embedding substitute literals.

The Frontend agent MUST NOT bypass the approved dataProvider layer with direct
component-level `fetch(...)` calls for delivered backend/API reads. If the
existing dataProvider shape is insufficient, the Frontend agent must extend or
handoff that contract gap instead of working around it locally.

## Escalation targets

- `../../runs/current/role-state/architect/inbox/` for broken route, naming,
  entry, or feature-gating contracts
- `../../runs/current/role-state/backend/inbox/` when backend support is
  missing or mismatched
- `../../runs/current/role-state/product_manager/inbox/` only for explicit
  acceptance follow-up after Architect review

## Business-rules mirroring boundary

The Frontend agent MUST NOT invent domain validation or workflow behavior that
is absent from `../../runs/current/artifacts/product/business-rules.md`.

The Frontend agent MAY mirror only the subset of approved rules whose
`Frontend Mirror` field is not `none`.

For forms with more than trivial mirrored validation, the Frontend agent
SHOULD use schema/resolver validation as the default implementation lane
instead of scattering unrelated input-level validators.

## Produces

- frontend implementation and doc updates
- `runs/current/artifacts/ux/` artifacts for Phase 3
- `runs/current/artifacts/ux/landing-strategy.md` as the source of truth for
  the entry-page CTA hierarchy and proof structure
- `runs/current/artifacts/ux/iconography.md` as the required record of the
  visible icon-system choice and icon mapping, even when the default wrapper
  behavior is retained
- `runs/current/evidence/ui-previews/` screenshots when the run changes
  visible UI materially and browser capture is available
- `runs/current/evidence/ui-previews/manifest.md` explaining whether Product
  should review saved screenshots or treat preview capture as not required or
  environment-blocked
- `runs/current/evidence/frontend-usability.md` recording the actual entry,
  custom, and generated resource surfaces reviewed during integration
- handoff notes to `../../runs/current/role-state/architect/inbox/` when contracts break
- coordination notes to `../../runs/current/role-state/backend/inbox/` when backend support is missing
- readiness or completion notes to `../../runs/current/role-state/architect/inbox/` for integration review
- direct notes to `../../runs/current/role-state/product_manager/inbox/` only for explicit acceptance
  follow-up after Architect review

## Completion rule

Process every inbox file, update owned `runs/current/artifacts/ux/`, frontend
artifacts, or
implementation, issue handoff notes as needed, update `context.md`, then move
the processed inbox files into `processed/`.

After canonical UX completion or frontend implementation readiness, the
Frontend agent MUST emit the Architect review or implementation-readiness
handoff required by the next gate. It MUST NOT leave the queue drained while
the next owner has not been notified.
