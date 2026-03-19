# Home And Entry

This file defines the always-on entry-page contract for generated apps.

The required run-owned artifact is:

- `../../runs/current/artifacts/ux/landing-strategy.md`

The generated app MUST implement that artifact through the primary entry page.

## Required Home page

Every generated app MUST include a `Home.tsx` page inside the normal
React-admin chrome.

`Home.tsx` MUST:

- remain reachable at `/app/#/Home`
- appear in the left sidebar with a visible home icon
- expose a visible title
- expose a real hero or landing region before any resource-grid or list-heavy
  content
- expose a one-sentence purpose or value statement
- expose the primary CTA defined by `landing-strategy.md`
- expose at least one proof, reassurance, or summary region above the fold or
  immediately after the hero
- answer the user-facing task described in `landing-strategy.md`, not internal
  implementation status

The primary entry surface MUST NOT default to a generated React-admin list
grid, generic datagrid shell, or starter resource index as the first
above-the-fold content. Resource lists may appear later on the page or behind
an explicit CTA, but they do not count as the required landing/hero surface.

`Home.tsx` MUST NOT ship as a contract viewer, route inventory page, or
recovery/debug shell. In particular, the primary entry page MUST NOT use
developer-facing copy about:

- `admin.yaml`
- provisional endpoint maps
- contract recovery
- schema/bootstrap restoration
- template or runtime cleanup

unless the run-owned UX artifacts explicitly approve an operator/debug entry
surface, which is not the baseline app behavior.

## Default entry behavior

`Home.tsx` is the default in-admin landing route unless the run-owned
architecture and UX artifacts explicitly approve a different primary entry
surface.

If the run overrides the default entry surface, the following MUST all agree:

- `../../runs/current/artifacts/architecture/route-and-entry-model.md`
- `../../runs/current/artifacts/ux/navigation.md`
- `../../runs/current/artifacts/ux/landing-strategy.md`

There MUST be exactly one declared primary entry route for the generated app.

## Entry-page implementation modes

The landing strategy MUST declare one of these modes:

- `Home only`
- `Home as dashboard`
- `Home + no-layout Landing`
- `CustomDashboard replaces starter Home content`

The landing strategy MUST also declare one starter pattern for `Home.tsx`:

- `hub`
- `dashboard`
- `landing`

If the run uses `Landing.tsx` or `CustomDashboard.tsx` as part of the real
entry experience, `Home.tsx` MUST still exist and MUST provide a visible path
into that approved entry flow.

Whether the run uses `Home only`, `Home as dashboard`, or a separate
`Landing.tsx`, the first meaningful user-facing screen MUST still begin with a
hero/landing treatment rather than a raw React-admin grid.

## Starter-compatibility rule

The shipped starter `Home.tsx` template is sufficient only when the run-owned
landing strategy explicitly marks the entry behavior as starter-compatible.

If the run requires richer proof surfaces, workflow shortcuts, role-specific
CTA behavior, or more than a trivial summary strip, the Frontend agent MUST
replace or extend the starter `Home.tsx`.

The starter pattern selected in `landing-strategy.md` MUST have direct visible
effect on the generated `Home.tsx`.

A run-owned `Home as dashboard` decision means the delivered `Home.tsx` MUST be
the real dashboard, not a temporary scaffold justified by later runtime work.

## Stable smoke-test hooks

The primary entry page SHOULD preserve stable selectors for smoke testing.

At minimum, the starter implementation SHOULD expose:

- `data-testid="entry-purpose"`
- `data-testid="entry-primary-cta"`
- `data-testid="entry-proof-strip"`

If a run replaces the starter entry component, the replacement SHOULD preserve
equivalent selectors or explicitly document an alternative smoke-test hook.
