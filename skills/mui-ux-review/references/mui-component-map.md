# MUI Pattern and Component Map

Use this file when recommending concrete component changes.

## 1. Page framing and layout

### Goal: Reduce cognitive load and create scanable structure

Prefer:

- `Container` to constrain line length and avoid ultra-wide text blocks
- `Box` for local grouping and spacing
- `Stack` for simple vertical or horizontal rhythm
- `Grid` for section layouts, form columns, and dashboard regions
- `Paper` for grouped surfaces without over-fragmenting the page
- `Card` only when a region is a true standalone unit
- `Divider` to separate sections with minimal chrome
- `Typography` with strong heading hierarchy

Avoid:

- full-width dense paragraphs in content-heavy pages
- wrapping every small fact in a separate `Card`
- mixed spacing systems that blur grouping
- decorative surfaces that compete with the main task

Notes:

- For content density, the first fix is usually layout and grouping, not a new widget.
- `Paper` is often a better fit than `Card` for utilitarian admin surfaces.

## 2. Progressive disclosure

### Goal: Show only what is needed by default

Prefer:

- `Accordion` for related optional sections when selective reading is useful
- `Collapse` for controlled reveal inside a known section
- `Drawer` for secondary controls or non-blocking side work
- `Dialog` for short blocking decisions or focused subflows
- `Popover` for compact contextual controls
- HTML `details/summary` only if you intentionally want the native pattern

Avoid:

- hiding instructions most users need
- forcing users to open many reveals to gather required facts
- putting long content inside a `Dialog`
- using `Tooltip` as a substitute for inline help

Decision rules:

- one short optional section -> `Collapse` or small `Accordion`
- multiple optional sections -> `Accordion`
- secondary controls that should preserve page context -> `Drawer`
- blocking confirmation or narrow task -> `Dialog`

## 3. Tabs, steppers, and navigation

### Goal: Separate views without increasing memory burden

Prefer:

- `Tabs` for peer views that are mutually exclusive
- `Stepper` for real multi-step flows
- `Breadcrumbs` for hierarchical context
- `Drawer` for app-level or sectional navigation when appropriate
- `Pagination` for long read-mostly result sets
- `BottomNavigation` only for mobile top-level destinations

Avoid:

- `Tabs` for step-by-step content
- `Tabs` when users need side-by-side comparison
- `Stepper` for short one-screen forms
- `Breadcrumbs` as a band-aid for weak page structure
- temporary drawers for required first-read content

Notes:

- If users need to compare sections, prefer one page with headings, or a compare table, over tabs.
- On small screens, scrollable tabs can work, but sections or accordion-style grouping may still be clearer.

## 4. Feedback, alerts, and transient status

### Goal: Keep users informed without forcing interpretation

Prefer:

- `Alert` for inline status, warnings, and validation summaries
- `Snackbar` for transient confirmations or completion notices
- `Snackbar` + `Alert` when transient feedback still needs severity semantics
- `Backdrop` sparingly for blocking async transitions that freeze the page
- `LinearProgress` for region or flow progress
- `CircularProgress` for compact indeterminate activity
- `Skeleton` for known-layout loading states

Avoid:

- silent saves or silent failures
- global snackbars for field-level errors
- skeletons that do not resemble the final layout
- long blocking backdrops without status text

Decision rules:

- persistent, must-read information -> `Alert`
- transient “saved” message -> `Snackbar`
- progress tied to a surface or step -> `LinearProgress`
- unknown wait without layout -> `CircularProgress`
- known layout still loading -> `Skeleton`

## 5. Forms and input choice

### Goal: Lower input effort and prevent errors

Prefer:

- `TextField` for free text and standard inputs
- `Autocomplete` for large or searchable option sets
- `Select` for small to medium fixed choices
- `RadioGroup` for a short set of mutually exclusive visible options
- `Checkbox` for multi-select or batch choices
- `Switch` for immediate binary settings
- `FormControl` and `FormHelperText` for label, helper, and error structure
- `InputAdornment` for units, currency, or scoped search cues
- `Stepper` only when the form truly benefits from staged progression

Avoid:

- `Select` with very large option sets
- burying rules in helper text
- unlabeled icon-only controls in forms
- split or repeated labels that increase scanning cost
- mixing immediate-save settings and submit-based fields without clear signaling

Notes:

- Use helper text for concise clarification, not policy dumps.
- If users repeatedly choose from long lists, `Autocomplete` is usually the right upgrade.

## 6. Data presentation

### Goal: Show dense information without overwhelming the user

Prefer:

- `DataGrid` (MUI X) for interactive, data-centric tables
- `Table` for simpler read-mostly tables
- `Chip` for statuses, tags, and compact categorical cues
- `Badge` for counts or notification marks
- `List` for medium-density item collections without full tabular needs
- `Avatar` sparingly for identity cues
- `Tooltip` only for terse, nonessential expansion

Avoid:

- raw IDs as primary labels
- wide tables without prioritization
- card grids where comparison is the main task
- putting essential row meaning in tooltips only
- over-coloring statuses without text labels

DataGrid vs Table:

Use `DataGrid` when you need several of:

- sorting
- filtering
- row selection
- sticky columns or pinning
- large datasets
- virtualization
- column visibility control

Use `Table` when:

- the table is small,
- the interaction model is simple,
- or MUI X is unavailable or unnecessary.

## 7. Empty, error, and loading states

### Goal: Replace dead ends with next steps

Compose empty states from:

- `Paper` or `Card`
- `Typography`
- `Button`
- optional icon or illustration
- optional `Alert` when the empty state is caused by an error or filter condition

For form-level errors:

- compose a top summary using `Alert`
- keep inline field errors in `FormHelperText`
- preserve the user’s entered values where possible

Avoid:

- blank surfaces
- “No data” with no next action
- error messages far from the field or action that caused them

## 8. Accessibility and responsive behavior

### Goal: Keep the UI understandable and operable across devices and input modes

Prefer:

- semantic heading structure via `Typography` and real heading elements
- visible focus states
- `useMediaQuery` to adapt density and layout
- `Stack` and `Grid` changes rather than shrinking everything
- `Drawer` variants chosen by breakpoint and task
- `Tabs` with clear selected state and manageable counts
- sufficient label text next to icons

Avoid:

- hover-only disclosure
- ambiguous icon-only navigation
- low-contrast active states
- desktop-only multi-column forms on mobile
- forcing users to horizontally scroll tables unless absolutely necessary

Responsive notes:

- collapse complex multi-column layouts to one column on small screens
- keep primary actions easy to reach
- move secondary controls behind a clearly labeled drawer only if they are truly secondary
