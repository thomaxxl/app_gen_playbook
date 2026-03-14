# UI System Change Policy

This file is maintainer-only guidance for playbook authors.

It defines how the starter UI system may be changed without destabilizing the
segmented playbook.

## Scope

This policy applies to changes in:

- `templates/app/frontend/theme.ts.md`
- `templates/app/frontend/PageHeader.tsx.md`
- `templates/app/frontend/EmptyState.tsx.md`
- `templates/app/frontend/ErrorState.tsx.md`
- `templates/app/frontend/FormSection.tsx.md`
- `templates/app/frontend/SummaryCard.tsx.md`
- starter page-shell usage in `Home.tsx.md`, `Landing.tsx.md`,
  `CustomDashboard.tsx.md`, and `SchemaDrivenAdminApp.tsx.md`

## Change rule

When the starter UI system changes, the maintainer MUST update, in the same
playbook change set:

- `../../specs/contracts/frontend/ui-principles.md`
- `../../specs/contracts/frontend/accessibility.md`
- `../../specs/contracts/frontend/theme-and-layout.md`
- `../../specs/contracts/frontend/validation.md`
- the affected starter templates under `../../templates/app/frontend/`

If the change affects run-owned UX artifact expectations, the maintainer MUST
also update the relevant files under:

- `../../specs/ux/`

## Segmentation rule

Feature-specific behavior MUST NOT be pushed into the starter UI system when
it belongs in:

- `../../specs/features/`
- `../../templates/features/`

If the change is relevant only to an optional capability, the maintainer MUST
create or update a feature pack instead of broadening the core UI contract.

## Validation rule

The maintainer MUST NOT treat a UI-system change as complete until:

- the affected frontend contracts are updated
- the affected templates are updated
- the frontend validation contract still matches the template behavior
- the playbook repo change is committed
