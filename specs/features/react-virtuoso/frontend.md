# React Virtuoso Frontend Guidance

Approved components:

- `Virtuoso`
- `GroupedVirtuoso`
- `TableVirtuoso`
- `VirtuosoGrid`

Feature-owned code MUST define:

- scroll-state ownership
- loading-row behavior
- empty-state behavior
- filtering/search interaction inside the virtualized surface

Virtualization plus drag/drop MUST NOT be assumed to work together unless a
future feature pack explicitly validates that combination.
