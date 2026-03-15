import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
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
  useRecordContext,
  useRedirect,
} from "react-admin";

import { useAdminSchema, useRawAdminYaml } from "./admin/schemaContext";
import {
  buildResourceMeta,
  type ResourceAttributeMeta,
  type ResourceMeta,
  type ResourceRelationshipMeta,
} from "./admin/resourceMetadata";

type SummaryItem =
  | { kind: "attribute"; attribute: ResourceAttributeMeta; key: string; label: string }
  | { kind: "relationship"; key: string; label: string; relationship: ResourceRelationshipMeta };

function isTruthyFlag(value: boolean | string | undefined): boolean {
  return value === true || value === "true";
}

function isHiddenSetting(
  hidden: boolean | string | undefined,
  mode: "show",
): boolean {
  if (isTruthyFlag(hidden)) {
    return true;
  }

  return typeof hidden === "string" && hidden.toLowerCase() === mode;
}

function isAttributeHidden(attribute: ResourceAttributeMeta): boolean {
  if (isHiddenSetting(attribute.hidden, "show")) {
    return true;
  }

  return attribute.show === false;
}

function isRelationshipHidden(relationship: ResourceRelationshipMeta): boolean {
  if (isHiddenSetting(relationship.hidden, "show")) {
    return true;
  }

  return relationship.hideShow === true;
}

function visibleAttributes(resourceMeta: ResourceMeta): ResourceAttributeMeta[] {
  return resourceMeta.attributes
    .filter((attribute) => !isAttributeHidden(attribute))
    .map((attribute, index) => ({ attribute, index }))
    .sort((left, right) => {
      const leftOrder = left.attribute.order;
      const rightOrder = right.attribute.order;

      if (leftOrder != null && rightOrder != null && leftOrder !== rightOrder) {
        return leftOrder - rightOrder;
      }

      if (leftOrder != null) {
        return -1;
      }

      if (rightOrder != null) {
        return 1;
      }

      return left.index - right.index;
    })
    .map(({ attribute }) => attribute);
}

function buildSummaryItems(resourceMeta: ResourceMeta): SummaryItem[] {
  const items: SummaryItem[] = [];
  const emittedRelationships = new Set<string>();

  for (const attribute of visibleAttributes(resourceMeta)) {
    if (
      attribute.relationship
      && attribute.relationship.direction === "toone"
      && !isRelationshipHidden(attribute.relationship)
    ) {
      if (emittedRelationships.has(attribute.relationship.name)) {
        continue;
      }

      emittedRelationships.add(attribute.relationship.name);
      items.push({
        kind: "relationship",
        key: `relationship:${attribute.relationship.name}`,
        label: attribute.relationship.label,
        relationship: attribute.relationship,
      });
      continue;
    }

    items.push({
      kind: "attribute",
      attribute,
      key: `attribute:${attribute.name}`,
      label: attribute.label,
    });
  }

  return items;
}

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

export function buildRelatedId(
  record: Record<string, unknown>,
  relationship: ResourceRelationshipMeta,
  delimiter: string,
): string | undefined {
  const values = relationship.fks
    .map((fk) => record[fk])
    .filter((value) => value !== undefined && value !== null && value !== "")
    .map((value) => String(value));

  if (values.length !== relationship.fks.length) {
    return undefined;
  }

  if (values.length === 1) {
    return values[0];
  }

  return values.join(relationship.compositeDelimiter ?? delimiter);
}

function formatScalarValue(value: unknown, kind: ResourceAttributeMeta["kind"]): string {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  if (kind === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  return String(value);
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
    if (preferred !== undefined && preferred !== null && preferred !== "") {
      return String(preferred);
    }
  }

  const fallback = relationship.fks
    .map((fk) => record[fk])
    .filter((value) => value !== undefined && value !== null && value !== "")
    .map((value) => String(value));

  return fallback.length > 0 ? fallback.join(" / ") : "-";
}

function SummaryGrid({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      style={{
        display: "grid",
        gap: "24px",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      }}
    >
      {children}
    </div>
  );
}

export function RelatedRecordSummary({
  data,
  resource,
}: {
  data: Record<string, unknown>;
  resource: string;
}) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useMemo(
    () => buildResourceMeta(schema, rawYaml, resource),
    [rawYaml, resource, schema],
  );
  const items = useMemo(
    () => buildSummaryItems(resourceMeta).slice(0, resourceMeta.maxListColumns),
    [resourceMeta],
  );

  return (
    <SummaryGrid>
      {items.map((item) => {
        let value = "-";

        if (item.kind === "relationship") {
          const targetMeta = buildResourceMeta(schema, rawYaml, item.relationship.targetResource);
          value = getRelatedRecordLabel(data, item.relationship, targetMeta);
        } else {
          value = formatScalarValue(data[item.attribute.name], item.attribute.kind);
        }

        return (
          <div key={item.key}>
            <Typography color="text.secondary" sx={{ fontWeight: 700, mb: 0.5 }} variant="body2">
              {item.label}
            </Typography>
            <Typography variant="body1">{value}</Typography>
          </div>
        );
      })}
    </SummaryGrid>
  );
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
  const dataProvider = useDataProvider();
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
  const label = useMemo(
    () => getRelatedRecordLabel(parentRecord, relationship, targetMeta),
    [parentRecord, relationship, targetMeta],
  );
  const canOpen = Boolean(embeddedRelated || relatedId);

  useEffect(() => {
    setRelated(embeddedRelated);
    setLoading(false);
    setError(null);
  }, [embeddedRelated, relatedId]);

  useEffect(() => {
    if (!open || embeddedRelated || !relatedId) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    dataProvider
      .getOne(relationship.targetResource, { id: relatedId })
      .then(({ data }) => {
        if (!cancelled) {
          setRelated(data as Record<string, unknown>);
          setLoading(false);
        }
      })
      .catch((nextError: unknown) => {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [dataProvider, embeddedRelated, open, relatedId, relationship.targetResource]);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!canOpen) {
      return;
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
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

  if (!canOpen || label === "-") {
    return <Typography component="span" variant="body2">{label}</Typography>;
  }

  return (
    <>
      <Button
        onClick={handleOpen}
        size="small"
        sx={{
          justifyContent: "flex-start",
          minWidth: 0,
          p: 0,
          textTransform: "none",
        }}
        variant="text"
      >
        {label}
      </Button>
      <Dialog fullWidth maxWidth="lg" onClose={handleClose} open={open}>
        <DialogTitle>{label}</DialogTitle>
        <DialogContent dividers>
          <div
            style={{
              display: "flex",
              gap: "8px",
              justifyContent: "flex-end",
              marginBottom: "24px",
            }}
          >
            <Button onClick={(event) => handleRedirect(event, "edit")} startIcon={<EditOutlinedIcon />}>
              EDIT
            </Button>
            <Button onClick={(event) => handleRedirect(event, "show")} startIcon={<KeyboardArrowRightIcon />}>
              VIEW
            </Button>
          </div>
          {loading ? <Loading /> : null}
          {!loading && error ? (
            <Typography color="error">{error}</Typography>
          ) : null}
          {!loading && !error && related ? (
            <RelatedRecordSummary data={related} resource={relationship.targetResource} />
          ) : null}
          {!loading && !error && !related ? (
            <Typography color="text.secondary">No related record.</Typography>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function SingleRelationshipTab({
  relationship,
}: {
  relationship: ResourceRelationshipMeta;
}) {
  const dataProvider = useDataProvider();
  const record = useRecordContext();
  const schema = useAdminSchema();
  const [related, setRelated] = useState<Record<string, unknown> | null>(() => {
    if (!record) {
      return null;
    }

    return getRecordRelationValue(record as Record<string, unknown>, relationship.name) ?? null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const relatedId = useMemo(
    () => record
      ? buildRelatedId(record as Record<string, unknown>, relationship, schema.delimiter)
      : undefined,
    [record, relationship, schema.delimiter],
  );

  useEffect(() => {
    if (!record) {
      return;
    }

    const embedded = getRecordRelationValue(
      record as Record<string, unknown>,
      relationship.name,
    );
    if (embedded) {
      setRelated(embedded);
      setLoading(false);
      setError(null);
      return;
    }

    if (!relatedId) {
      setRelated(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    dataProvider
      .getOne(relationship.targetResource, { id: relatedId })
      .then(({ data }) => {
        if (!cancelled) {
          setRelated(data as Record<string, unknown>);
          setLoading(false);
        }
      })
      .catch((nextError: unknown) => {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [dataProvider, record, relatedId, relationship]);

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <Typography color="error" sx={{ pt: 2 }}>
        {error}
      </Typography>
    );
  }

  if (!related) {
    return (
      <Typography color="text.secondary" sx={{ pt: 2 }}>
        No related record.
      </Typography>
    );
  }

  return <RelatedRecordSummary data={related} resource={relationship.targetResource} />;
}

function getRelationshipPriority(
  relationship: ResourceRelationshipMeta,
  parentResource: string,
): number {
  if (relationship.direction === "tomany" && relationship.targetResource !== parentResource) {
    return 0;
  }

  if (relationship.direction === "toone" && relationship.targetResource !== parentResource) {
    return 1;
  }

  if (relationship.direction === "tomany") {
    return 2;
  }

  return 3;
}

export function getDefaultRelationshipTabIndex(
  relationships: ResourceRelationshipMeta[],
  parentResource: string,
): number {
  if (relationships.length === 0) {
    return 0;
  }

  let bestIndex = 0;
  let bestPriority = Number.POSITIVE_INFINITY;

  relationships.forEach((relationship, index) => {
    const priority = getRelationshipPriority(relationship, parentResource);
    if (priority < bestPriority) {
      bestPriority = priority;
      bestIndex = index;
    }
  });

  return bestIndex;
}
