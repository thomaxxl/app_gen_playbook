# Accessibility

This file defines the minimum accessibility contract for generated frontends.

It is a core frontend contract. The Frontend role MUST treat it as required
implementation input, not as optional polish.

## Baseline

Generated apps MUST target WCAG 2.1 / 2.x AA as the current implementation
baseline.

WCAG 3.0 MAY be used as forward-looking guidance, but it MUST NOT replace the
current WCAG 2.x AA baseline in implementation or validation language.

## Keyboard access

The UI MUST remain operable by keyboard for the core user flows.

At minimum:

- navigation links MUST be reachable
- form inputs MUST be reachable in a logical order
- dialogs MUST support keyboard focus entry and exit
- dialog dismissal MUST return focus to a sensible origin when practical
- custom no-layout pages MUST NOT introduce keyboard traps

## Visible focus

Interactive elements MUST expose visible focus styling.

Focus indicators MUST remain visible against the chosen theme colors and MUST
NOT rely only on color changes too subtle to notice.

## Forms and error clarity

Forms MUST provide:

- visible labels
- required-field indication when applicable
- clear field-level or section-level error messaging
- inline validation language that explains what the user should correct

Error copy MUST remain task-oriented and MUST NOT expose raw implementation
details as the primary user message.

## Contrast and semantic color

Theme choices MUST preserve readable contrast for:

- body text
- headings
- button labels
- helper text
- error and success states

Color MUST NOT be the only carrier of critical meaning when text or icon
support is practical.

## Icons, images, and charts

Icons, images, charts, and visual summaries MUST preserve a text-level cue
when they communicate meaning relevant to task completion.

At minimum:

- icon-only controls MUST expose an accessible name
- custom charts MUST expose a visible title or caption
- custom charts MUST provide a readable fallback summary when the chart is the
  only place the user would otherwise learn a key result
- uploaded images or media previews MUST not become the sole carrier of
  required business information

## State orientation

After save, error, or destructive confirmation flows, the UI SHOULD keep the
user oriented.

When practical, the frontend SHOULD restore focus or position the user near:

- the saved result
- the first failing field
- the reopened list or detail page

## Evaluation model

Accessibility checks MUST happen throughout the run, not only at final QA.

At minimum:

- Phase 3 MUST record any non-default accessibility expectations in the
  run-owned UX artifacts
- Phase 5 MUST include keyboard/focus smoke validation for the critical flows
- final Playwright validation MUST include at least a lightweight keyboard and
  visible-state check for the core path

Higher-risk apps or explicitly accessibility-focused runs MAY require stronger
evaluation, but the baseline checks above are mandatory for every generated
app.
