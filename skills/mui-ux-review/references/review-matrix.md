# Review Matrix

Use this file when you need a fast but structured pass across the page.

| Category | What to check | Why it matters | Relevant MUI components/patterns |
|---|---|---|---|
| Layout | Is the page purpose obvious at first glance? | Users need to orient immediately. | `Typography`, `Paper`, `Box`, `Stack` |
| Layout | Is there a clear primary action? | Weak action hierarchy causes hesitation. | `Button`, `ButtonGroup`, summary header composition |
| Layout | Are sections chunked and easy to scan? | Chunking reduces cognitive load. | `Container`, `Grid`, `Stack`, `Divider`, `Paper` |
| Layout | Is content width readable rather than edge-to-edge? | Very wide text becomes hard to scan. | `Container`, `Box`, responsive width constraints |
| Layout | Is the page overloaded with low-value cards or modules? | Excess modules bury the task path. | `Paper`, `Card`, `Accordion` |
| Navigation | Can the user tell where they are? | Weak orientation increases backtracking. | `Breadcrumbs`, `Drawer`, headings |
| Navigation | Do local sections or tabs match the user’s mental model? | Poor sectional navigation increases memory burden. | `Tabs`, sectioned `Paper`, anchor links |
| Navigation | Are tabs being used for comparison or step-by-step reading? | Tabs hide content and make comparison expensive. | Prefer visible sections or compare tables over `Tabs` |
| Navigation | Are reveal labels specific? | Weak information scent makes hidden content easy to miss. | `Accordion`, `Collapse`, `Drawer`, `Popover` |
| Content & Readability | Does copy start with what to do now? | Task-first writing reduces friction. | `Typography`, local summary blocks |
| Content & Readability | Is helper text short and local? | Long helper text is skipped or overwhelms screen readers. | `FormHelperText`, visible helper blocks |
| Content & Readability | Are jargon and internal codes minimized? | Users should not decode internal language mid-task. | `Autocomplete`, labels, `Chip`, inline definitions |
| Content & Readability | Are large blocks broken into bullets or subsections? | Scannable content is processed faster than walls of text. | `List`, `Typography`, `Divider` |
| Interaction & Feedback | Does the page show loading, saving, success, and failure clearly? | Hidden state creates uncertainty and duplicate actions. | `Skeleton`, `LinearProgress`, `CircularProgress`, `Snackbar`, `Alert` |
| Interaction & Feedback | Are destructive actions separated and confirmed? | Prevents costly mistakes. | `Dialog`, danger-styled `Button`, `Alert` |
| Interaction & Feedback | Are dialogs or drawers narrow in scope? | Overlays become disorienting when overloaded. | `Dialog`, `Drawer`, `Popover` |
| Interaction & Feedback | Is there a recovery path after mistakes? | Reversible flows reduce user anxiety and error cost. | `Snackbar` with undo, `Dialog`, inline `Alert` |
| Forms | Are fields grouped by mental model? | Grouping lowers form comprehension cost. | `Grid`, `Stack`, `Paper`, `Divider` |
| Forms | Is the input type appropriate to the choice set? | Wrong controls increase input effort and mistakes. | `TextField`, `Autocomplete`, `Select`, `RadioGroup`, `Checkbox`, `Switch` |
| Forms | Are labels self-sufficient without relying on helper text? | Labels must carry the core meaning. | `TextField`, `FormControl`, `FormHelperText` |
| Forms | Are errors close to fields and summarized when necessary? | Clear recovery reduces abandonment. | `FormHelperText`, top-of-form `Alert`, field error states |
| Forms | Is the form staged only when it genuinely helps? | Unnecessary staging adds friction. | `Stepper`, sectioned form layout |
| Data Presentation | Does the data surface support comparison? | Comparison is a core reason to use rows and columns. | `DataGrid`, `Table`, `List` |
| Data Presentation | Are the right columns visible by default? | Too many columns slow decisions. | `DataGrid`, `Table`, `Chip`, `Typography` |
| Data Presentation | Are statuses readable without relying on color alone? | Status must remain scannable and accessible. | `Chip`, `Badge`, text labels |
| Data Presentation | Are raw IDs replacing meaningful labels? | Raw IDs destroy scanability and comprehension. | linked labels, `Autocomplete`, `Dialog`, `Drawer`, `Chip` |
| Data Presentation | Are filters visible enough but not overwhelming? | Hidden or overloaded filters both hurt task speed. | `Drawer`, `Popover`, `Menu`, filter summary `Chip`s |
| Accessibility | Is heading order logical and semantic? | Screen-reader and keyboard navigation rely on structure. | semantic headings with `Typography` |
| Accessibility | Is the page operable from keyboard? | Core task flow must not depend on pointer use. | `Tabs`, `Dialog`, `Drawer`, `Accordion`, `Menu` |
| Accessibility | Are icon-only controls labeled? | Ambiguous controls are unusable for many users. | accessible labels, `Tooltip` only as optional help |
| Accessibility | Are key meanings conveyed beyond color? | Color-only cues are inaccessible and brittle. | `Alert`, `Chip`, text labels |
| Performance & States | Does loading resemble the final layout when possible? | Good perceived performance reduces confusion. | `Skeleton`, `LinearProgress` |
| Performance & States | Does every empty state explain what happened and what to do next? | Empty states should not be dead ends. | composed `Paper`/`Card` + `Typography` + `Button` |
| Performance & States | Is heavy hidden content slowing the page? | Hiding content is not a performance fix by itself. | split routes, defer content, lighter `Accordion`/`Tabs` usage |
| Mobile Responsiveness | Does the layout collapse cleanly to one column when needed? | Mobile comprehension depends on stable hierarchy. | breakpoint `Grid`, `Stack`, `useMediaQuery` |
| Mobile Responsiveness | Are tabs, drawers, and tables still usable on small screens? | Desktop patterns often break on mobile. | scrollable `Tabs`, `Drawer`, alternative list views |
| Mobile Responsiveness | Does the primary action remain easy to reach and understand? | Small screens magnify action-discovery problems. | sticky/fixed action areas, clear `Button` hierarchy |
