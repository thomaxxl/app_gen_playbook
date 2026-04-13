# Relationship Surface Plan

Use this template when related entities are poorly surfaced.

## Relationships to fix

| Relationship | Current problem | User task affected | Proposed surface | MUI recommendation |
|---|---|---|---|---|
| | | | | |

## Rules

- Replace raw foreign keys with meaningful labels.
- Keep high-frequency related facts visible.
- Use overlays only when they reduce, not increase, context switching.

## Surface decisions

### In-row or inline

Use when:
- users need fast scanning,
- the relationship is central to the list or detail page,
- and a short label is enough.

Recommended MUI:
- `Chip`
- linked `Typography`
- compact `List`
- inline summary `Paper`

### Dialog

Use when:
- the user needs a focused child preview or quick action,
- but should return to the current page immediately.

Recommended MUI:
- `Dialog`
- `DialogTitle`
- `DialogContent`
- `DialogActions`

### Drawer

Use when:
- the user benefits from preserving page context while inspecting or editing a related item.

Recommended MUI:
- `Drawer`
- sectioned content with `Stack` or `Grid`

### Tabs or sections

Use when:
- the related entity is a stable part of the parent record.

Recommended MUI:
- `Tabs`
- `Paper`
- `DataGrid`
- `List`

## Priority fixes

1. [...]
2. [...]
3. [...]
