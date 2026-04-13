# Exhaustive Page Review Checklist

Use this file for a full audit. Cover every category. Prioritize findings in the final output.

For each item, ask:

- What is the user trying to do here?
- Does the current design help or slow that task?
- If this is a problem, what is the MUI-appropriate fix?

---

## A. Layout and information architecture

### 1. Page purpose and entry clarity

- [ ] Is the page purpose obvious within a few seconds?
- [ ] Is the page title specific and meaningful?
- [ ] Is the primary action obvious without scrolling or searching?
- [ ] Does the top section answer “what is this?”, “what matters?”, and “what can I do?”
- [ ] Is background or explanatory content demoted below the main task when appropriate?

Relevant MUI patterns:

- `Typography`
- `Paper`
- `Card`
- `Box`
- `Stack`
- `Divider`

### 2. Visual hierarchy and grouping

- [ ] Are sections clearly chunked?
- [ ] Do headings describe the content below them?
- [ ] Is there a predictable scan path?
- [ ] Are primary controls visually stronger than secondary ones?
- [ ] Is dense text broken into smaller units?
- [ ] Is content width readable rather than edge-to-edge?

Relevant MUI patterns:

- `Container`
- `Grid`
- `Stack`
- `Box`
- `Typography`
- `Divider`

### 3. Density and clutter

- [ ] Is the page carrying more regions, cards, or modules than the task needs?
- [ ] Are there duplicate summaries or duplicate actions?
- [ ] Is important content pushed down by low-value chrome?
- [ ] Is progressive disclosure being used to solve a writing problem that should be solved by restructuring?

Relevant MUI patterns:

- `Paper`
- `Card`
- `Accordion`
- `Collapse`

---

## B. Navigation and orientation

### 4. Global and local navigation

- [ ] Can the user tell where they are in the product?
- [ ] Is there a clear path back to the previous level or parent entity?
- [ ] Are local page sections navigable without guesswork?
- [ ] Does navigation compete with content?

Relevant MUI patterns:

- `Breadcrumbs`
- `Drawer`
- `Tabs`
- `Menu`
- `Link`

### 5. Tabs and sectional navigation

- [ ] Are tabs truly peer sections?
- [ ] Would the user need to compare across tabs?
- [ ] Are tab labels short and specific?
- [ ] Are there too many tabs?
- [ ] On mobile, do tabs remain understandable and usable?

Relevant MUI patterns:

- `Tabs`

Flag as High when comparison across tabs is likely.

### 6. Progressive disclosure and hidden content

- [ ] Is hidden content optional for most users?
- [ ] Are reveal labels specific enough to create strong information scent?
- [ ] Would most users open the hidden content?
- [ ] Is essential information buried in accordions, drawers, dialogs, or tooltips?
- [ ] Would visible headings work better than hidden sections?

Relevant MUI patterns:

- `Accordion`
- `Collapse`
- `Drawer`
- `Dialog`
- `Popover`
- `Tooltip`

Flag as Critical when required information is hidden.

---

## C. Content and readability

### 7. Task-first writing

- [ ] Does copy start with what the user needs to know or do now?
- [ ] Is the page free of “everything we know” background text?
- [ ] Are labels and headings concrete rather than abstract?
- [ ] Is jargon minimized or defined when unavoidable?

Relevant MUI patterns:

- `Typography`
- `FormHelperText`
- `Tooltip` (nonessential only)

### 8. Chunking and scanability

- [ ] Are paragraphs short?
- [ ] Are bullet lists used where users scan for rules or steps?
- [ ] Are large blocks split into one-idea sections?
- [ ] Is helper text short and local?

Relevant MUI patterns:

- `Typography`
- `List`
- `Box`
- `Divider`

### 9. Recognition over recall

- [ ] Does the page show choices, examples, or recent context instead of forcing memory?
- [ ] Are cryptic codes replaced or supplemented with meaningful labels?
- [ ] Are option sets searchable when large?

Relevant MUI patterns:

- `Autocomplete`
- `Select`
- `Chip`
- `List`
- `Tooltip` (brief only)

---

## D. Interaction and feedback

### 10. Call-to-action clarity

- [ ] Is the primary action obvious?
- [ ] Are secondary actions visually subordinate?
- [ ] Are destructive actions distinct and clearly labeled?
- [ ] Are buttons action-oriented rather than generic?

Relevant MUI patterns:

- `Button`
- `ButtonGroup`
- `Dialog`
- `Alert`

### 11. System status and save behavior

- [ ] Does the user know when something is loading, saving, or failed?
- [ ] Is autosave vs explicit save obvious?
- [ ] After saving, is feedback visible and proportional?
- [ ] Are long-running actions explained?

Relevant MUI patterns:

- `Snackbar`
- `Alert`
- `LinearProgress`
- `CircularProgress`
- `Backdrop`
- `Skeleton`

### 12. Overlay quality

- [ ] Is each dialog or drawer justified?
- [ ] Is the overlay scope narrow and clear?
- [ ] Does the title explain the task?
- [ ] Does the overlay preserve enough context?
- [ ] Are there nested overlays or unnecessary blocking steps?

Relevant MUI patterns:

- `Dialog`
- `Drawer`
- `Popover`
- `Menu`

Flag as High when overlays create context-switch burden.

### 13. Undo, recovery, and reversibility

- [ ] Can the user recover from mistakes?
- [ ] Are destructive actions confirmed?
- [ ] Is there an undo path where sensible?
- [ ] Is cancel behavior predictable?

Relevant MUI patterns:

- `Dialog`
- `Snackbar`
- `Alert`

---

## E. Forms

### 14. Form structure

- [ ] Are fields grouped by mental model?
- [ ] Is the form staged only when it truly helps?
- [ ] Are advanced fields demoted appropriately?
- [ ] Is the form free of giant undifferentiated field walls?

Relevant MUI patterns:

- `Grid`
- `Stack`
- `Box`
- `Divider`
- `Paper`
- `Card`
- `Stepper`

### 15. Labels, helper text, and requiredness

- [ ] Are labels specific and complete on their own?
- [ ] Is requiredness visible and consistent?
- [ ] Is helper text short and actually helpful?
- [ ] Are critical instructions visible in the label or main body instead of helper text?

Relevant MUI patterns:

- `TextField`
- `FormControl`
- `FormHelperText`

### 16. Input type fit

- [ ] Is each input type appropriate to the data and decision?
- [ ] Are large option sets using `Autocomplete` rather than long selects?
- [ ] Are short mutually exclusive choices visible as radios where that improves scanability?
- [ ] Are switches used only for immediate binary settings?

Relevant MUI patterns:

- `TextField`
- `Autocomplete`
- `Select`
- `RadioGroup`
- `Checkbox`
- `Switch`

### 17. Validation and errors

- [ ] Are errors close to the source?
- [ ] Is there a top-level summary when the form is long or multi-error?
- [ ] Are messages specific and fixable?
- [ ] Is validation timing respectful rather than hostile?
- [ ] Is the user’s input preserved on error?

Relevant MUI patterns:

- `FormHelperText`
- `Alert`
- `TextField`

Flag as Critical when users can easily miss blocking validation.

### 18. Submission flow

- [ ] Is the save or submit action easy to find?
- [ ] Are secondary actions separated from the main submit?
- [ ] Is the next step obvious after submission?
- [ ] Are draft/save-and-return expectations clear when relevant?

Relevant MUI patterns:

- `Button`
- `ButtonGroup`
- `Stepper`
- `Snackbar`
- `Alert`

---

## F. Data presentation

### 19. Table and grid fit

- [ ] Is the page using a table or grid when comparison is the real task?
- [ ] Are the visible columns the ones users actually decide from?
- [ ] Are row actions discoverable?
- [ ] Are long values truncated intelligently with a safe expansion path?
- [ ] Is the dataset large enough to justify `DataGrid`?

Relevant MUI patterns:

- `DataGrid`
- `Table`
- `Tooltip` (nonessential only)
- `Chip`
- `Menu`

### 20. Density and row semantics

- [ ] Are statuses, dates, owners, and amounts easy to scan?
- [ ] Are raw IDs avoided?
- [ ] Are status cues textual and not color-only?
- [ ] Is row density appropriate to user throughput?

Relevant MUI patterns:

- `Chip`
- `Badge`
- `Typography`
- `Avatar`

### 21. Filters and sorting

- [ ] Are the right filters visible by default?
- [ ] Are secondary filters grouped without overwhelming the page?
- [ ] Does the page summarize active filters?
- [ ] Is sort state obvious?

Relevant MUI patterns:

- `Drawer`
- `Popover`
- `Menu`
- `Autocomplete`
- `Chip`
- `DataGrid`

### 22. Related entities and admin relationships

- [ ] Are related entities shown with meaningful labels instead of IDs?
- [ ] Can the user navigate or inspect the relationship without losing context?
- [ ] Are related lists surfaced where the task needs them?
- [ ] Is the page forcing too much navigation between parent and child data?

Relevant MUI patterns:

- `Autocomplete`
- `Dialog`
- `Drawer`
- `Tabs`
- `List`
- `DataGrid`
- `Table`

Use `references/admin-resource-rules.md` for detailed judgment here.

---

## G. Accessibility

### 23. Semantics and heading structure

- [ ] Is heading order logical?
- [ ] Are sections navigable by assistive technology?
- [ ] Are icon-only controls labeled?
- [ ] Are layout primitives being used without losing semantics?

Relevant MUI patterns:

- `Typography`
- `Tooltip`
- composed semantic containers

### 24. Keyboard and focus flow

- [ ] Can the page be operated without a mouse?
- [ ] Is focus visible?
- [ ] Do tabs, dialogs, drawers, accordions, and menus behave predictably from keyboard input?
- [ ] Does focus return sensibly after overlay close?

Relevant MUI patterns:

- `Tabs`
- `Dialog`
- `Drawer`
- `Accordion`
- `Menu`
- `Popover`
- `Tooltip`

Flag as Critical when core task flow is keyboard-hostile.

### 25. Color, contrast, and non-color cues

- [ ] Are status meanings textual and not color-only?
- [ ] Are active or selected states strong enough?
- [ ] Is disabled state still readable and understandable?
- [ ] Is error or warning meaning conveyed beyond hue?

Relevant MUI patterns:

- `Alert`
- `Chip`
- `Tabs`
- `Button`
- `Typography`

### 26. Motion, timing, and hover dependence

- [ ] Is key information available without hover?
- [ ] Are transitions helping rather than hiding meaning?
- [ ] Are snackbars readable and not disappearing too quickly for the context?
- [ ] Are tooltips optional rather than required for comprehension?

Relevant MUI patterns:

- `Tooltip`
- `Snackbar`
- transition components

---

## H. Performance and states

### 27. Loading and perceived performance

- [ ] Does the page communicate that work is happening?
- [ ] Is the loading pattern appropriate to the layout?
- [ ] Is heavy hidden content making the page feel sluggish?
- [ ] Are there obvious opportunities to stage or defer secondary content?

Relevant MUI patterns:

- `Skeleton`
- `LinearProgress`
- `CircularProgress`
- `Backdrop`

### 28. Empty, partial, and error states

- [ ] Does every important data surface have an empty state?
- [ ] Do empty states explain why there is no content?
- [ ] Is the best next action offered?
- [ ] Do partial failures surface clearly?

Relevant MUI patterns:

- composed `Paper`/`Card` empty state
- `Alert`
- `Button`

### 29. Resilience of hidden or secondary content

- [ ] If tabs, drawers, or accordions fail to open, is the user blocked?
- [ ] Are secondary surfaces doing work that the main page should do?
- [ ] Would a simple inline section be more robust?

Relevant MUI patterns:

- `Accordion`
- `Tabs`
- `Drawer`
- `Dialog`

---

## I. Mobile responsiveness

### 30. Breakpoint behavior

- [ ] Does the layout collapse cleanly to one column where needed?
- [ ] Are cards, filters, and tables still usable on small screens?
- [ ] Does the primary action stay visible?
- [ ] Are dialogs or drawers too large or too deep for the screen?

Relevant MUI patterns:

- `useMediaQuery`
- `Grid`
- `Stack`
- `Drawer`
- `Dialog`
- `Tabs`

### 31. Small-screen navigation and density

- [ ] Are tabs still understandable on mobile?
- [ ] Would stacked sections be clearer than horizontal tabs?
- [ ] Are touch targets adequate?
- [ ] Is the page forcing horizontal scrolling for core actions or understanding?

Relevant MUI patterns:

- `Tabs`
- `BottomNavigation`
- `Drawer`
- `Accordion`

### 32. Mobile data views

- [ ] If a table is present, is it still readable on mobile?
- [ ] Should the representation change instead of simply shrinking the same table?
- [ ] Are important statuses and identifiers preserved in the reduced view?

Relevant MUI patterns:

- `DataGrid`
- `Table`
- `List`
- `Card`
- `Chip`

---

## J. Final synthesis checks

Before finalizing a review:

- [ ] Did you tie every major finding to a user goal?
- [ ] Did you separate root-cause issues from polish issues?
- [ ] Did you avoid recommending hidden content unless justified?
- [ ] Did you name concrete MUI components or composed patterns?
- [ ] Did you flag hidden required information, inaccessible controls, and destructive-risk issues appropriately?
- [ ] Did you avoid over-prescribing visual style changes with weak UX payoff?
