# Resource View Strategy

Use this template when a review shows that a resource-oriented admin area needs structural redesign.

## Resource

- **Resource name:** [...]
- **Resource class:** [reference / transactional / parent-aggregate / join-history / singleton-settings]
- **Primary user roles:** [...]
- **Primary tasks:** [...]

## Current problems

- [...]
- [...]
- [...]

## Recommended view model

### List view

- Purpose:
- Key columns or row signals:
- Required filters:
- Bulk actions:
- Row actions:
- MUI pattern recommendation: [`DataGrid` / `Table` / `List` + support components]

### Detail view

- Top summary should show:
- Related entities that must be visible:
- Activity or history surface:
- MUI pattern recommendation: [`Paper`, `Tabs`, `List`, `DataGrid`, `Alert`, ...]

### Create/edit view

- Core sections:
- Advanced sections:
- Related entities in form:
- Validation risks:
- MUI pattern recommendation: [`Grid`, `Stack`, `Autocomplete`, `Stepper`, ...]

## Things to remove or demote

- [...]
- [...]

## Priority changes

1. [...]
2. [...]
3. [...]
