# `frontend/src/shared-runtime/relationshipUi.tsx`

See also:

- [../../../../specs/contracts/frontend/relationship-ui.md](../../../../specs/contracts/frontend/relationship-ui.md)
- [../../../../specs/contracts/frontend/record-shape.md](../../../../specs/contracts/frontend/record-shape.md)
- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [admin/resourceMetadata.ts.md](admin/resourceMetadata.ts.md)
- [resourceRegistry.tsx.md](resourceRegistry.tsx.md)

This helper module centralizes the Northwind-style relationship UI contract.

The generated runtime SHOULD keep relationship-specific behavior here rather
than scattering it across list/show components.

Read-side rule:

- prefer embedded related objects from canonical `include=...`
- otherwise prefer the canonical SAFRS parent relationship route
- only then fall back to `dataProvider.getOne(...)` by id

This helper MUST NOT become a reason to invent side endpoints for ordinary
DB-backed related data that SAFRS already exposes.

Required exports SHOULD include:

- `getRecordRelationValue(...)`
- `buildRelatedId(...)`
- `getRelatedRecordLabel(...)`
- `RelatedRecordDialogLink`
- `RelatedRecordSummary`
- `SingleRelationshipTab`
- `getDefaultRelationshipTabIndex(...)`

```tsx
import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import {
  Loading,
  useDataProvider,
  useRedirect,
  useRecordContext,
} from "react-admin";

import { useAdminSchema, useRawAdminYaml } from "./admin/schemaContext";
import {
  buildResourceMeta,
  type ResourceMeta,
  type ResourceRelationshipMeta,
} from "./admin/resourceMetadata";

type ExecuteCapableDataProvider = ReturnType<typeof useDataProvider> & {
  execute?: (request: {
    method?: string;
    mode?: "raw" | "jsonapi";
    path: string;
  }) => Promise<unknown>;
};

export function getRecordRelationValue(
  record: Record<string, unknown>,
  relationshipName: string,
): Record<string, unknown> | undefined {
  const direct = record[relationshipName];
  if (direct && typeof direct === "object" && !Array.isArray(direct)) {
    return direct as Record<string, unknown>;
  }

  const alias = record[`rel_${relationshipName}`];
  if (alias && typeof alias === "object" && !Array.isArray(alias)) {
    return alias as Record<string, unknown>;
  }

  return undefined;
}

export function getRelatedRecordLabel(
  record: Record<string, unknown>,
  relationship: ResourceRelationshipMeta,
  targetMeta: ResourceMeta,
): string {
  const related = getRecordRelationValue(record, relationship.name);
  if (related) {
    const labelField = targetMeta.userKey ?? "name";
    const preferred = related[labelField] ?? related.name ?? related.id;
    if (preferred != null && preferred !== "") {
      return String(preferred);
    }
  }

  const fallback = relationship.fks
    .map((fk) => record[fk])
    .filter((value) => value != null && value !== "")
    .map((value) => String(value));

  return fallback.length > 0 ? fallback.join(" / ") : "-";
}

export function buildRelatedId(
  record: Record<string, unknown>,
  relationship: ResourceRelationshipMeta,
  delimiter: string,
): string | undefined {
  const values = relationship.fks
    .map((fk) => record[fk])
    .filter((value) => value != null && value !== "")
    .map((value) => String(value));

  if (values.length !== relationship.fks.length) {
    return undefined;
  }

  return values.length === 1
    ? values[0]
    : values.join(relationship.compositeDelimiter ?? delimiter);
}

function buildRelationshipRoutePath(
  relationship: ResourceRelationshipMeta,
  parentRecord: Record<string, unknown>,
): string | null {
  const parentId = parentRecord.id;
  if (parentId === undefined || parentId === null || parentId === "") {
    return null;
  }

  return relationship.relationshipRouteTemplate.replace(
    "{id}",
    encodeURIComponent(String(parentId)),
  );
}

function extractRelationshipRecord(payload: unknown): Record<string, unknown> | null {
  const document = payload as {
    data?: unknown;
  } | null;

  const related = document?.data;
  if (related && typeof related === "object" && !Array.isArray(related)) {
    return related as Record<string, unknown>;
  }

  return null;
}

export function RelatedRecordDialogLink({
  parentRecord,
  relationship,
}: {
  parentRecord: Record<string, unknown>;
  relationship: ResourceRelationshipMeta;
}) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const dataProvider = useDataProvider() as ExecuteCapableDataProvider;
  const redirect = useRedirect();
  const targetMeta = useMemo(
    () => buildResourceMeta(schema, rawYaml, relationship.targetResource),
    [rawYaml, relationship.targetResource, schema],
  );
  const embeddedRelated = useMemo(
    () => getRecordRelationValue(parentRecord, relationship.name) ?? null,
    [parentRecord, relationship.name],
  );
  const [open, setOpen] = useState(false);
  const [related, setRelated] = useState<Record<string, unknown> | null>(embeddedRelated);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const relatedId = useMemo(
    () => buildRelatedId(parentRecord, relationship, schema.delimiter),
    [parentRecord, relationship, schema.delimiter],
  );
  const relationshipRoutePath = useMemo(
    () => buildRelationshipRoutePath(relationship, parentRecord),
    [parentRecord, relationship],
  );
  const label = useMemo(
    () => getRelatedRecordLabel(parentRecord, relationship, targetMeta),
    [parentRecord, relationship, targetMeta],
  );

  useEffect(() => {
    if (!open || embeddedRelated) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        if (relationshipRoutePath && typeof dataProvider.execute === "function") {
          const routePayload = await dataProvider.execute({
            path: relationshipRoutePath,
            method: "GET",
            mode: "raw",
          });
          const routeRecord = extractRelationshipRecord(routePayload);
          if (routeRecord) {
            if (!cancelled) {
              setRelated(routeRecord);
              setLoading(false);
            }
            return;
          }
        }

        if (!relatedId) {
          throw new Error("Missing related id and no embedded or relationship-route payload was available.");
        }

        const result = await dataProvider.getOne(relationship.targetResource, { id: relatedId });
        if (!cancelled) {
          setRelated(result.data as Record<string, unknown>);
          setLoading(false);
        }
      } catch (nextError: unknown) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [
    dataProvider,
    embeddedRelated,
    open,
    relatedId,
    relationship.targetResource,
    relationshipRoutePath,
  ]);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!relatedId && !embeddedRelated) {
      return;
    }
    setOpen(true);
  };

  const handleRedirect = (
    event: React.MouseEvent<HTMLButtonElement>,
    mode: "edit" | "show",
  ) => {
    event.preventDefault();
    event.stopPropagation();
    if (!relatedId) {
      return;
    }
    setOpen(false);
    redirect(mode, relationship.targetResource, relatedId);
  };

  if (label === "-") {
    return <Typography component="span" variant="body2">{label}</Typography>;
  }

  return (
    <>
      <Button onClick={handleOpen} size="small" sx={{ minWidth: 0, p: 0, textTransform: "none" }}>
        {label}
      </Button>
      <Dialog fullWidth maxWidth="lg" onClose={() => setOpen(false)} open={open}>
        <DialogTitle>{label}</DialogTitle>
        <DialogContent dividers>
          <Button onClick={(event) => handleRedirect(event, "edit")} startIcon={<EditOutlinedIcon />}>
            EDIT
          </Button>
          <Button onClick={(event) => handleRedirect(event, "show")} startIcon={<KeyboardArrowRightIcon />}>
            VIEW
          </Button>
          {loading ? <Loading /> : null}
          {!loading && error ? <Typography color="error">{error}</Typography> : null}
          {!loading && !error && related ? (
            <RelatedRecordSummary data={related} resource={relationship.targetResource} />
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function RelatedRecordSummary({
  data,
  resource,
}: {
  data: Record<string, unknown>;
  resource: string;
}) {
  // Reuse the same metadata-driven summary rendering as the generated show page.
  return <div>{resource}</div>;
}

export function SingleRelationshipTab({
  relationship,
}: {
  relationship: ResourceRelationshipMeta;
}) {
  const record = useRecordContext<Record<string, unknown>>();
  if (!record) {
    return <Loading />;
  }

  // Fetch or reuse the embedded related record, then render RelatedRecordSummary.
  return <div>{relationship.label}</div>;
}
```

Implementation notes:

- `RelatedRecordSummary` and `SingleRelationshipTab` are intentionally reduced
  above; the generated app MUST replace the placeholders with the actual
  metadata-driven summary rendering
- the dialog opener MUST call both `preventDefault()` and `stopPropagation()`
  so it does not trigger datagrid row navigation
- id-based `dataProvider.getOne(...)` fallback is acceptable only after the
  runtime has tried embedded include data and the canonical parent
  relationship route, typically through `dataProvider.execute(...)`
- the list/show runtime MUST use this module instead of ad hoc per-page
  relationship rendering
- the runtime SHOULD keep `getDefaultRelationshipTabIndex(...)` here so the
  default-tab priority stays centralized
- this helper MUST consume the same raw-`admin.yaml`-backed relationship
  metadata produced by `admin/resourceMetadata.ts`, not a separate ad hoc
  relationship lookup path
- this module MUST assume `ResourceRelationshipMeta` may contain
  fallback-synthesized relationships rather than only relationships declared
  completely by the normalizer
