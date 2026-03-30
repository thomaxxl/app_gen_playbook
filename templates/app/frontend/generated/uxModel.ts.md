# `frontend/src/generated/uxModel.ts`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../../specs/ux/resource-view-strategy.md](../../../../specs/ux/resource-view-strategy.md)
- [../../../../specs/ux/relationship-surface-plan.md](../../../../specs/ux/relationship-surface-plan.md)
- [../../../../specs/ux/form-grouping-plan.md](../../../../specs/ux/form-grouping-plan.md)
- [../../../../specs/ux/dashboard-data-plan.md](../../../../specs/ux/dashboard-data-plan.md)

This file is the executable frontend UX model compiled from the run-owned UX
artifact package. It exists so generated runtime code does not have to guess
layout decisions from prose.

```ts
export type EntrySurfaceMode = "dashboard" | "hub" | "landing";
export type ResourceUiClass =
  | "lookup/reference"
  | "transactional"
  | "parent-aggregate"
  | "join/history"
  | "settings/singleton";
export type RelationshipSurface =
  | "chip-list"
  | "dialog-preview"
  | "show-tab"
  | "inline-summary-panel"
  | "dedicated-page-only";
export type FormLayout = "compact" | "mixed" | "wide";
export type ShowVariant = "minimal" | "overview+tabs" | "dashboard-first";

export interface FormSectionConfig {
  title: string;
  description?: string;
  fields: string[];
  layout?: FormLayout;
}

export interface RelationshipSurfaceConfig {
  surface?: RelationshipSurface;
  summaryBehavior?: string;
  defaultAction?: string;
}

export interface ResourceUxConfig {
  uiClass?: ResourceUiClass;
  listColumnBudget?: number;
  listFields?: string[];
  showOverviewFields?: string[];
  showVariant?: ShowVariant;
  relationshipProminence?: "low" | "normal" | "high";
  groupedForms?: boolean;
  formSections?: FormSectionConfig[];
  dashboardRelevance?: "none" | "supporting" | "primary";
  relationships?: Record<string, RelationshipSurfaceConfig>;
}

export interface EntrySurfaceConfig {
  mode: EntrySurfaceMode;
  starterCompatible?: boolean;
  title?: string;
  primaryCtaLabel?: string;
}

export interface UxModel {
  entrySurface: EntrySurfaceConfig;
  resources: Record<string, ResourceUxConfig>;
}

const UX_MODEL: UxModel = {
  entrySurface: {
    mode: "dashboard",
    starterCompatible: false,
  },
  resources: {},
};

export function getEntrySurfaceConfig(): EntrySurfaceConfig {
  return UX_MODEL.entrySurface;
}

export function getResourceUxConfig(resource: string): ResourceUxConfig {
  return UX_MODEL.resources[resource] ?? {};
}

export default UX_MODEL;
```

Notes:

- Replace the default contents with run-specific values derived from:
  - `runs/current/artifacts/ux/resource-view-strategy.md`
  - `runs/current/artifacts/ux/relationship-surface-plan.md`
  - `runs/current/artifacts/ux/form-grouping-plan.md`
  - `runs/current/artifacts/ux/dashboard-data-plan.md`
  - `runs/current/artifacts/ux/landing-strategy.md`
- The runtime MUST treat this file as executable surface policy, not as
  another optional helper.
- Keep this file small and durable. Put high-level defaults here and keep
  volatile runtime field metadata in `admin.yaml` plus
  `shared-runtime/admin/resourceMetadata.ts`.
