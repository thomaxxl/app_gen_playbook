# Admin and Resource-Oriented Review Rules

Use this file when the product is a data-heavy admin app, internal tool, CRUD application, or resource-oriented workflow.

## Core rule

Do not evaluate an admin page as if it were a marketing page or lightweight consumer screen.

Admin users often need:

- higher information density,
- faster scanning,
- multiple related facts visible at once,
- and fewer context switches.

The goal is not minimal UI. The goal is high-throughput, low-error task execution.

## Cross-cutting rules

### 1. Never surface raw relationship IDs as primary labels

Flag as **High** or **Critical** when:

- a list row shows `customerId`, `projectId`, `ownerId`, etc. instead of a meaningful label,
- a detail page shows foreign keys without a related label or navigation path,
- or a form asks the user to choose an opaque ID.

Prefer:

- human-readable labels,
- `Autocomplete` for relationship selection,
- linked labels that open `Dialog`, `Drawer`, or related detail routes,
- `Chip` or compact label formatting for status-like relationships.

### 2. Dashboards must be workflow-relevant

Flag as **High** when the home page is generic card filler with no operational value.

A useful dashboard should surface:

- queues,
- anomalies,
- pending approvals,
- stale items,
- failures,
- and the next likely action.

Prefer:

- compact summary regions using `Paper`, `Card`, `Typography`, `List`, `Chip`, and `Alert`,
- tables or lists for actionable queues,
- short trend or status summaries only when they support action.

Avoid:

- decorative charts with no next action,
- duplicate summary cards,
- and dashboards that hide the real work behind another click.

### 3. Forms must be sectioned

Flag as **High** when a resource form is one long undifferentiated field wall.

Prefer:

- sections grouped by user mental model,
- `Grid` two-column layout on desktop when it reduces scrolling and preserves comprehension,
- one-column mobile layout,
- clear primary and secondary actions,
- related sub-entity management in dedicated sections or tabs when necessary.

Avoid:

- mixing identifiers, status, metadata, and business fields without structure,
- giant “advanced settings” dumps,
- and deeply nested dialogs for normal editing.

### 4. Keep required related facts visible

Flag as **Critical** when the user must open many reveals to compare essential information.

Prefer:

- visible summary regions,
- tabs only for true peer sections,
- sub-entity lists in-place when they are central to the task,
- and a stable layout where key status, ownership, timing, and recent activity are visible together.

Avoid:

- accordion ladders for required facts,
- comparison across tabs,
- or detail pages that force note-taking.

## Resource-class playbooks

## A. Reference or lookup resource

Examples:

- countries
- categories
- tax codes
- tags
- status definitions

Good fit:

- simple list + simple form
- fewer columns
- labels and descriptions visible
- light detail surfaces or inline editing where safe

Review for:

- unnecessary complexity
- over-engineered dashboards
- poor naming
- lack of search or filtering if the list is long

## B. Transactional resource

Examples:

- orders
- invoices
- tickets
- cases
- claims

Good fit:

- list view with status, owner, dates, and amount or priority visible
- detail view with timeline/history and action zone
- forms that separate core fields from operational metadata

Review for:

- hidden status transitions,
- weak confirmation around destructive or state-changing actions,
- poor queueing and filtering,
- missing activity or history surface.

## C. Parent or aggregate resource

Examples:

- account
- customer
- project
- organization

Good fit:

- detail page with summary at top
- child entities surfaced as tabs or clear sections
- recent activity visible
- quick actions for common child workflows

Review for:

- fragmented navigation to child data,
- summary that omits the most important facts,
- inability to understand account health at a glance.

## D. Join, history, or audit resource

Examples:

- memberships
- mappings
- event logs
- audit logs
- sync records

Good fit:

- table-first or timeline-first presentation
- strong filtering and date or actor context
- minimal form surfaces unless editing is real

Review for:

- fake CRUD patterns where a log should just be a data view,
- unreadable metadata,
- missing traceability,
- poor sorting or filter affordances.

## E. Singleton settings or configuration resource

Examples:

- billing settings
- tenant settings
- feature flags
- integration settings

Good fit:

- sectioned settings page
- short explanatory summaries
- clear save behavior
- confirmation for destructive changes
- defaults and validation visible

Review for:

- unclear save model,
- too much helper text,
- missing confirmation or rollback clues,
- settings grouped by implementation instead of user mental model.

## Planning artifacts to generate when reviewing a larger app

If the review spans multiple resources, generate these artifacts when they help:

- `assets/resource-view-strategy-template.md`
- `assets/relationship-surface-plan-template.md`
- `assets/dashboard-data-plan-template.md`
- `assets/form-grouping-plan-template.md`

Use them to move from critique to an execution-ready redesign plan.
