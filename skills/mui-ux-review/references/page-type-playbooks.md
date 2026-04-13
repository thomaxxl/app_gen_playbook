# Page-Type Playbooks

Use this file after classifying the page.

## 1. Dashboard or home page

### What good looks like

- The user immediately sees what matters today.
- The page answers “what needs attention?” before “what exists?”
- Summary content is short and decision-oriented.
- Actionable queues are visible without extra digging.

### Common failures

- card soup with low-value stats
- charts without follow-up actions
- generic placeholders
- too much narrative text above the actual work

### MUI fits

- `Paper` or `Card` for meaningful summary regions
- `Typography` + `List` for short action queues
- `Alert` for urgent anomalies
- `Chip` for compact status cues
- `DataGrid`, `Table`, or `List` for actionable queues

## 2. List, table, or search results page

### What good looks like

- The table or list prioritizes the columns that drive decisions.
- Filters are discoverable but not overwhelming.
- Row affordances are obvious.
- Status, ownership, dates, and identifiers are readable at scan speed.

### Common failures

- too many columns
- raw IDs
- hidden actions that require guesswork
- filters buried without summary
- card layouts where tabular comparison is needed

### MUI fits

- `DataGrid` for interactive or large datasets
- `Table` for simpler read-mostly data
- `Chip` for status
- `Drawer` or `Popover` for secondary filters
- `Breadcrumbs` when hierarchy matters
- `Pagination` when list length justifies it

## 3. Detail or record page

### What good looks like

- The top section establishes identity, status, and the next likely action.
- Supporting information is grouped by mental model.
- Related entities and recent activity are easy to inspect.
- Required facts do not require multiple hidden reveals.

### Common failures

- weak summary header
- too many accordions
- tabs that require comparison
- related info split across many surfaces
- history or activity missing

### MUI fits

- `Paper` summary region
- `Tabs` only for true peer sections
- `List`, `Table`, or `DataGrid` for related items
- `Dialog` or `Drawer` for focused child actions
- `Chip`, `Badge`, and `Alert` for status context

## 4. Create or edit form

### What good looks like

- Fields are grouped into clear sections.
- The primary action is obvious.
- Validation is local and understandable.
- The form does not front-load irrelevant detail.

### Common failures

- giant field wall
- weak labels
- long helper text
- no separation between core fields and advanced options
- unclear save model
- missing dirty-state or success feedback

### MUI fits

- `Grid`, `Stack`, `Box`, `Divider`, `Paper`
- `TextField`, `Autocomplete`, `Select`, `Checkbox`, `RadioGroup`, `Switch`
- `FormControl` + `FormHelperText`
- `Alert` for summary validation or save status
- `Stepper` only when the form truly benefits from staging

## 5. Settings or preferences page

### What good looks like

- Settings are grouped by intent, not by backend implementation.
- Immediate-change controls feel different from submit-based controls.
- Risky actions are clearly isolated.
- Defaults and consequences are visible.

### Common failures

- mixed save model
- too much policy text inline
- destructive settings mixed with ordinary ones
- poor section headings

### MUI fits

- `Paper` or `Card` sections
- `Switch` for immediate toggles
- `TextField`/`Select`/`Autocomplete` for submitted settings
- `Dialog` for risky confirms
- `Alert` for context or risk

## 6. Wizard or multi-step flow

### What good looks like

- The current step and remaining effort are obvious.
- Each step focuses on one stage of the task.
- Users can recover from mistakes without losing context.
- Step content is not overloaded.

### Common failures

- stepper used for a short one-screen form
- unstable step count
- too much content per step
- missing save-and-return cues
- back and next actions that compete with many secondary buttons

### MUI fits

- `Stepper`
- `LinearProgress` when a simpler progress model is better
- sectioned forms within each step
- `Alert` for blocking guidance or validation summary

## 7. Dialog or drawer workflow

### What good looks like

- The overlay has a narrow purpose.
- Users understand why it is separate from the page.
- Critical context is preserved or repeated.
- Closing behavior is predictable.

### Common failures

- long forms in dialogs
- drawers used for required first-read content
- nested overlays
- weak titles and no clear primary action

### MUI fits

- `Dialog` for focused blocking tasks
- `Drawer` for side work, filters, or non-blocking edit surfaces
- `Alert` inside the overlay when risk or error context matters

## 8. Empty, error, and loading states

### What good looks like

- The state explains what happened.
- The user has a next step.
- The loading pattern matches the final layout.
- Errors are close to the source and easy to recover from.

### Common failures

- blank surfaces
- generic “something went wrong”
- no recovery path
- spinners with no context
- skeletons that mislead

### MUI fits

- composed empty state from `Paper`/`Card` + `Typography` + `Button`
- `Alert` for errors or filter-empty explanations
- `Skeleton`, `LinearProgress`, `CircularProgress`
- `Snackbar` only for transient confirmations, not core failure explanation

## 9. Mobile review pass

After any page-specific review, run a mobile pass.

Check:

- Does the primary action stay discoverable?
- Does layout collapse sensibly to one column?
- Do tabs still work or should sections become stacked?
- Are drawers or filters clearly labeled?
- Are tables still understandable or is a different representation needed?
- Are touch targets and spacing sufficient?

Useful MUI tools:

- `useMediaQuery`
- breakpoint-driven `Grid` and `Stack`
- scrollable `Tabs`
- `Drawer` variants
- `BottomNavigation` only for top-level mobile navigation
