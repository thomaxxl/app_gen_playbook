---
name: mui-ux-review
description: Review and critique the UX/UI of web pages, screenshots, and MUI/React interfaces. Use when asked to audit a screen, page, workflow, dashboard, admin UI, list/detail view, form, dialog, or data-heavy application; identify usability issues; reduce text overload and cognitive load; and map improvements to concrete Material UI components and patterns.
---

# MUI UX Review

Review a page or flow, identify the highest-leverage UX/UI issues, and recommend concrete fixes that fit Material UI and MUI X.

## Core stance

- Judge the default path first.
- Prioritize task success, clarity, accessibility, and resilience over visual novelty.
- Treat hidden content as a trade-off, not a free layout trick.
- Do not recommend a component swap unless it improves information architecture, interaction cost, or comprehension.
- For data-dense operator or admin screens, do not blindly apply consumer-app minimalism.

## Input collection

Collect or infer:

- Review target: screenshot(s), URL, code snippet, or plain-language description.
- Page type: dashboard/home, list/table, detail, create/edit form, settings, wizard, search/filter, dialog/drawer overlay, empty/error/loading, or data-heavy admin page.
- User goal: what the person is trying to accomplish on this screen.
- Frequency and skill level: novice, occasional, operator, expert.
- Device emphasis: desktop, mobile, or both.
- Constraints: MUI-only, MUI X allowed, accessibility requirements, readonly vs edit-heavy, regulatory or destructive-action concerns.

If information is missing, infer cautiously and state assumptions.

## Review modes

Choose the lightest mode that fits the request:

1. **Quick review**
   - Use for a single screenshot or a casual critique request.
   - Return the top 5–8 highest-leverage issues only.

2. **Full page audit**
   - Use for a serious page review.
   - Read `references/review-checklist.md`.
   - Cover every category, but still prioritize findings.

3. **Flow or multi-page audit**
   - Use when reviewing a workflow or several pages.
   - Read `references/review-checklist.md`, `references/page-type-playbooks.md`, and `references/report-template.md`.
   - If the product is a resource-oriented admin app, also read `references/admin-resource-rules.md`.
   - When useful, generate the planning artifacts from `assets/`.

## Required workflow

1. **Classify the page**
   - Identify page type and task type before judging components.
   - If the page is mixed (for example: dashboard + table + filter drawer), review each major region separately.

2. **Audit the first 5 seconds**
   - Check whether the page quickly answers:
     - What is this page?
     - What can I do here?
     - What matters most right now?
   - Note anything that competes with those answers.

3. **Review the default path**
   - Follow the main action path before reviewing edge cases.
   - Determine whether the user can complete the primary task without opening extra panels, tabs, tooltips, or dialogs.

4. **Run the checklist**
   - Always read `references/review-checklist.md` for a full audit.
   - Read `references/review-matrix.md` when you want a compact structured sweep by category.
   - Read `references/page-type-playbooks.md` after classifying the page.
   - Read `references/mui-component-map.md` when suggesting component-level fixes.
   - Read `references/admin-resource-rules.md` if the page is resource/entity/admin/data-heavy.
   - Read `references/report-template.md` before finalizing the response.

5. **Identify root causes**
   - Distinguish between:
     - information architecture problems,
     - content density problems,
     - interaction problems,
     - state/feedback problems,
     - accessibility problems,
     - and purely visual polish issues.
   - Fix root causes before recommending cosmetic cleanup.

6. **Map fixes to MUI**
   - Recommend concrete MUI or MUI X components, patterns, and layout primitives.
   - Name the component family explicitly.
   - Explain why the suggested component is a better fit.
   - If MUI does not provide a first-class component, say so and recommend a composed pattern.

7. **Prioritize**
   - Use this severity scale:
     - **Critical**: likely task failure, destructive mistake, required information hidden, inaccessible interaction, or severe misinterpretation.
     - **High**: major slowdown, repeated confusion, comparison burden, or missing status/feedback.
     - **Medium**: recoverable friction or comprehension cost.
     - **Low**: polish or local inefficiency.
   - Prefer a few strong findings over many weak nits.

## MUI-specific decision rules

Apply these rules unless the page context gives a strong reason not to.

### Progressive disclosure and structure

- Use `Accordion` or `Collapse` only for content that is truly optional for many users.
- Do not hide majority-needed instructions inside `Accordion`, `Tooltip`, or a secondary `Drawer`.
- Use `Tabs` only for peer sections where simultaneous visibility is not needed.
- Do not use `Tabs` for sequential reading or side-by-side comparison.
- Use `Stepper` only for genuine multi-step flows.
- For must-not-miss summary content, compose a summary area from `Paper`, `Card`, `Typography`, `List`, `Chip`, and short supporting text.

### Overlays and secondary surfaces

- Use `Dialog` for short, blocking decisions, confirmations, or focused subflows.
- Prefer a `Drawer` for secondary controls, filters, or edit surfaces that benefit from preserving page context.
- Do not force the user to open many dialogs or drawers to collate essential information.
- Use `Popover` or `Menu` for compact, local, non-document workflows.
- Use `Tooltip` only for brief, nonessential clarification.

### Feedback and states

- Use `Alert` for persistent inline status, risk, or validation summaries.
- Use `Snackbar` for transient confirmation or completion feedback; combine with `Alert` when severity matters.
- Use `Skeleton` when the layout is known and data is loading.
- Use `LinearProgress` or `CircularProgress` for active operations; prefer `LinearProgress` when progress belongs to a region or flow.
- Compose empty states with `Paper` or `Card` plus `Typography`, a clear next action, and optional iconography.

### Forms

- Use `TextField`, `FormControl`, `FormHelperText`, `Select`, `Autocomplete`, `Checkbox`, `RadioGroup`, and `Switch` according to option count and task semantics.
- Prefer `Autocomplete` for large or searchable option sets.
- Prefer `Select` or `RadioGroup` for small, fixed choices.
- Prefer `Switch` for immediate on/off settings and `Checkbox` for multi-select or form submission.
- Keep helper text short; do not bury critical instructions in helper text.
- Use `Grid`, `Stack`, `Box`, `Divider`, `Paper`, and `Card` to create clear form sections.

### Data-heavy views

- Prefer `DataGrid` (MUI X) for dense, interactive datasets with sorting, filtering, selection, pagination, pinning, or virtualization needs.
- Use `Table` only when the tabular interaction model is simple and the dataset is modest.
- Use `Chip`, `Badge`, and `Typography` to compress status and categorical meaning without turning the page into card soup.
- Use `Breadcrumbs` for hierarchy, not as the primary fix for poor page structure.

## Evidence standard

Every finding must include:

- the affected screen region or element,
- what the user is likely trying to do,
- what gets in the way,
- why it matters,
- and a concrete fix.

Avoid generic statements like:

- “the UX could be better”
- “the page is cluttered”
- “the hierarchy is weak”

Replace them with precise, local observations.

## What not to do

- Do not nitpick colors, spacing, or typography unless they affect comprehension, scannability, affordance, or accessibility.
- Do not recommend tooltips for required content.
- Do not recommend tabs when comparison is required.
- Do not recommend accordions when most users need the content.
- Do not replace data-heavy operator screens with decorative card grids.
- Do not propose dialogs for long-form editing when a full page or drawer is clearer.
- Do not recommend more text as a fix when a structural change is the real solution.

## Output requirements

Use the structure in `references/report-template.md`.

Minimum response contents:

1. Context and assumptions
2. Overall verdict
3. Prioritized findings with severity
4. Concrete MUI-oriented fixes
5. Quick wins vs structural changes
6. Follow-up checks or experiments when useful

For each finding, include:

- **Severity**
- **Category**
- **Evidence**
- **Why it matters**
- **Recommended change**
- **Relevant MUI components or patterns**

## Multi-page or admin-app audits

If the user is reviewing a larger admin app, produce one or more of these artifacts when they would improve execution clarity:

- `assets/resource-view-strategy-template.md`
- `assets/relationship-surface-plan-template.md`
- `assets/dashboard-data-plan-template.md`
- `assets/form-grouping-plan-template.md`

Use them when the review reveals structural issues that span multiple resources or pages.

## Escalation rules

Escalate a finding to **Critical** when any of these are true:

- required information is hidden behind interaction,
- a destructive action lacks clear confirmation or reversibility,
- a validation or error state is easy to miss,
- keyboard or screen-reader use is materially blocked,
- or the page is likely to cause incorrect data entry or irreversible user mistakes.

Escalate to **High** when:

- the user must compare across tabs or hidden sections,
- the page forces repeated context switching,
- the main call to action competes with secondary content,
- or the user cannot easily tell what changed, saved, failed, or loaded.

## Final check before responding

Before finalizing, verify that:

- findings are tied to a page type and user goal,
- fixes are concrete and MUI-specific,
- the report is prioritized,
- hidden-content recommendations are justified,
- and no critical or high-severity issue is buried under cosmetic notes.
