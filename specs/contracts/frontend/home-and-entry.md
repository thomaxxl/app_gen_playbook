# Home And Entry

This file defines the always-on entry-page contract for generated apps.

The required run-owned artifact is:

- `../../runs/current/artifacts/ux/landing-strategy.md`

The generated app MUST implement that artifact through the primary entry page.

## Required Home page

Every generated app MUST include a `Home.tsx` page inside the normal
React-admin chrome.

`Home.tsx` MUST:

- remain reachable at `/admin-app/#/Home`
- appear in the left sidebar with a visible home icon
- expose a visible title
- expose a one-sentence purpose or value statement
- expose the primary CTA defined by `landing-strategy.md`
- expose at least one proof, reassurance, or summary region above the fold or
  immediately after the hero

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

If the run uses `Landing.tsx` or `CustomDashboard.tsx` as part of the real
entry experience, `Home.tsx` MUST still exist and MUST provide a visible path
into that approved entry flow.

## Starter-compatibility rule

The shipped starter `Home.tsx` template is sufficient only when the run-owned
landing strategy explicitly marks the entry behavior as starter-compatible.

If the run requires richer proof surfaces, workflow shortcuts, role-specific
CTA behavior, or more than a trivial summary strip, the Frontend agent MUST
replace or extend the starter `Home.tsx`.

## Stable smoke-test hooks

The primary entry page SHOULD preserve stable selectors for smoke testing.

At minimum, the starter implementation SHOULD expose:

- `data-testid="entry-purpose"`
- `data-testid="entry-primary-cta"`
- `data-testid="entry-proof-strip"`

If a run replaces the starter entry component, the replacement SHOULD preserve
equivalent selectors or explicitly document an alternative smoke-test hook.
