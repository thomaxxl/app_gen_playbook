# `frontend/src/shared-runtime/resourceRegistry.tsx`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../specs/contracts/frontend/admin-yaml-contract.md)
- [../../../../specs/contracts/frontend/relationship-ui.md](../../../../specs/contracts/frontend/relationship-ui.md)
- [relationshipUi.tsx.md](relationshipUi.tsx.md)

```tsx
import { useEffect, useMemo, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import { Box, Divider, Tab, Tabs, Typography } from "@mui/material";
import {
  AutocompleteInput,
  BooleanField,
  BooleanInput,
  Create,
  Datagrid,
  DateField,
  DateInput,
  DeleteWithConfirmButton,
  ListContextProvider,
  Edit,
  EditButton,
  FunctionField,
  List,
  Loading,
  NumberField,
  NumberInput,
  ReferenceInput,
  Resource,
  SearchInput,
  Show,
  SimpleForm,
  TextField,
  TextInput,
  useDataProvider,
  useList,
  useRecordContext,
} from "react-admin";
import type { SafrsDataProvider, Schema } from "safrs-jsonapi-client";

import { useAdminSchema, useRawAdminYaml } from "./admin/schemaContext";
import {
  buildResourceMeta,
  type RawAdminYaml,
  type ResourceAttributeMeta,
  type ResourceMeta,
  type ResourceRelationshipMeta,
  useResourceMeta,
} from "./admin/resourceMetadata";
import {
  extractExecuteRecords,
  getRecordRelationValues,
  getDefaultRelationshipTabIndex,
  type RelationshipLoadSource,
  RelationshipResolutionAlert,
  RelatedRecordDialogLink,
  resolveRelationshipExecuteRequest,
  SingleRelationshipTab,
  sortRelatedRecords,
} from "./relationshipUi";

const DEFAULT_PAGE_SIZE = 25;

type DisplayMode = "create" | "edit" | "list" | "show";

type DisplayItem =
  | { kind: "attribute"; attribute: ResourceAttributeMeta; key: string; label: string }
  | { kind: "relationship"; key: string; label: string; relationship: ResourceRelationshipMeta };

export interface ResourcePages {
  name: string;
  list: () => ReactElement;
  create: () => ReactElement;
  edit: () => ReactElement;
  show: () => ReactElement;
  recordRepresentation?: string;
}

export function makeSchemaDrivenPages(resourceName: string): ResourcePages {
  const ListPage = () => <SchemaDrivenList resource={resourceName} />;
  const ShowPage = () => <SchemaDrivenShow resource={resourceName} />;
  const EditPage = () => <SchemaDrivenEdit resource={resourceName} />;
  const CreatePage = () => <SchemaDrivenCreate resource={resourceName} />;

  ListPage.displayName = `${resourceName}List`;
  ShowPage.displayName = `${resourceName}Show`;
  EditPage.displayName = `${resourceName}Edit`;
  CreatePage.displayName = `${resourceName}Create`;

  return {
    name: resourceName,
    list: ListPage,
    show: ShowPage,
    edit: EditPage,
    create: CreatePage,
  };
}

function isTruthyFlag(value: boolean | string | undefined): boolean {
  return value === true || value === "true";
}

function isHiddenSetting(
  hidden: boolean | string | undefined,
  mode: DisplayMode,
): boolean {
  if (isTruthyFlag(hidden)) {
    return true;
  }

  return typeof hidden === "string" && hidden.toLowerCase() === mode;
}

function isAttributeHidden(attribute: ResourceAttributeMeta, mode: DisplayMode): boolean {
  if (isHiddenSetting(attribute.hidden, mode)) {
    return true;
  }

  const explicitVisibility = (
    mode === "list"
      ? attribute.list
      : mode === "show"
        ? attribute.show
        : mode === "create"
          ? attribute.create
          : attribute.edit
  );

  return explicitVisibility === false;
}

function isRelationshipHidden(
  relationship: ResourceRelationshipMeta,
  mode: "list" | "show",
): boolean {
  if (isHiddenSetting(relationship.hidden, mode)) {
    return true;
  }

  if (mode === "list" && relationship.hideList === true) {
    return true;
  }

  if (mode === "show" && relationship.hideShow === true) {
    return true;
  }

  return false;
}

function visibleAttributes(
  resourceMeta: ResourceMeta,
  mode: DisplayMode,
): ResourceAttributeMeta[] {
  return resourceMeta.attributes
    .filter((attribute) => !isAttributeHidden(attribute, mode))
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

function visibleDisplayItems(
  resourceMeta: ResourceMeta,
  mode: "list" | "show",
): DisplayItem[] {
  const items: DisplayItem[] = [];
  const emittedRelationships = new Set<string>();

  for (const attribute of visibleAttributes(resourceMeta, mode)) {
    if (
      attribute.relationship
      && attribute.relationship.direction === "toone"
      && !isRelationshipHidden(attribute.relationship, mode)
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

function buildSearchPlaceholder(resourceMeta: ResourceMeta): string {
  const labels = resourceMeta.searchColumns.map((column) => column.label);
  if (labels.length === 0) {
    return "Search";
  }
  if (labels.length === 1) {
    return `Search ${labels[0]}`;
  }
  if (labels.length === 2) {
    return `Search ${labels[0]} or ${labels[1]}`;
  }
  return `Search ${labels.slice(0, 3).join(", ")}`;
}

function getFormColumnSpan(attribute: ResourceAttributeMeta): number {
  const fieldName = attribute.name.toLowerCase();

  if (attribute.fullWidth || attribute.formSpan === 12) {
    return 12;
  }

  if (attribute.formSpan != null) {
    return attribute.formSpan;
  }

  if (attribute.widget === "textarea") {
    return 12;
  }

  if (
    attribute.isPrimaryKey
    || attribute.kind === "boolean"
    || attribute.kind === "number"
    || fieldName.endsWith("_id")
    || fieldName.endsWith("id")
    || fieldName.endsWith("_code")
    || fieldName.endsWith("code")
    || fieldName.includes("count")
    || fieldName.includes("total")
    || fieldName.includes("score")
    || fieldName.includes("value")
    || fieldName.includes("limit")
  ) {
    return 3;
  }

  return 4;
}

function getTextareaRows(attribute: ResourceAttributeMeta): number {
  return attribute.rows ?? 4;
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

function renderListField(
  item: DisplayItem,
  schema: Schema,
) {
  if (item.kind === "relationship") {
    return (
      <FunctionField
        key={item.key}
        label={item.label}
        render={(record: Record<string, unknown>) => (
          <RelatedRecordDialogLink
            parentRecord={record}
            relationship={item.relationship}
            surface="list"
          />
        )}
      />
    );
  }

  const attribute = item.attribute;

  if (attribute.kind === "number") {
    return <NumberField key={item.key} label={item.label} source={attribute.name} />;
  }

  if (attribute.kind === "boolean") {
    return <BooleanField key={item.key} label={item.label} source={attribute.name} />;
  }

  if (attribute.kind === "date") {
    return <DateField key={item.key} label={item.label} source={attribute.name} />;
  }

  return <TextField key={item.key} label={item.label} source={attribute.name} />;
}

function renderInput(
  attribute: ResourceAttributeMeta,
  schema: Schema,
  rawYaml: RawAdminYaml,
) {
  if (attribute.readonly) {
    return null;
  }

  const relationship = attribute.relationship;
  if (relationship && relationship.direction === "toone" && relationship.fks[0] === attribute.name) {
    const targetMeta = buildResourceMeta(schema, rawYaml, relationship.targetResource);
    return (
      <ReferenceInput
        key={attribute.name}
        label={relationship.label}
        reference={relationship.targetResource}
        source={attribute.name}
      >
        <AutocompleteInput
          fullWidth
          label={relationship.label}
          optionText={targetMeta.userKey ?? "id"}
        />
      </ReferenceInput>
    );
  }

  if (attribute.reference) {
    const targetMeta = buildResourceMeta(schema, rawYaml, attribute.reference);
    return (
      <ReferenceInput
        key={attribute.name}
        label={attribute.label}
        reference={attribute.reference}
        source={attribute.name}
      >
        <AutocompleteInput
          fullWidth
          label={attribute.label}
          optionText={targetMeta.userKey ?? "id"}
        />
      </ReferenceInput>
    );
  }

  const commonProps = {
    key: attribute.name,
    label: attribute.label,
    required: attribute.required,
    source: attribute.name,
  };

  if (attribute.kind === "number") {
    return <NumberInput {...commonProps} />;
  }

  if (attribute.kind === "boolean") {
    return <BooleanInput {...commonProps} />;
  }

  if (attribute.kind === "date") {
    return <DateInput {...commonProps} />;
  }

  if (attribute.widget === "textarea") {
    return <TextInput {...commonProps} multiline minRows={getTextareaRows(attribute)} />;
  }

  return <TextInput {...commonProps} />;
}

function renderFormItem(
  attribute: ResourceAttributeMeta,
  schema: Schema,
  rawYaml: RawAdminYaml,
) {
  const input = renderInput(attribute, schema, rawYaml);
  if (!input) {
    return null;
  }

  return (
    <Box
      key={`form:${attribute.name}`}
      sx={{
        gridColumn: {
          xs: "1 / -1",
          md: `span ${getFormColumnSpan(attribute)}`,
        },
      }}
    >
      {input}
    </Box>
  );
}

function OverviewGrid({
  items,
  resourceMeta,
}: {
  items: DisplayItem[];
  resourceMeta: ResourceMeta;
}) {
  const record = useRecordContext<Record<string, unknown>>();

  if (!record) {
    return <Loading />;
  }

  return (
    <Box>
      <Typography sx={{ mb: 4 }} variant="h4">
        {resourceMeta.label}{" "}
        <Box component="span" sx={{ color: "text.secondary", fontStyle: "italic" }}>
          #{String(record.id ?? "")}
        </Box>
      </Typography>
      <Box
        sx={{
          display: "grid",
          gap: 3,
          gridTemplateColumns: {
            xs: "minmax(0, 1fr)",
            md: "repeat(4, minmax(0, 1fr))",
          },
        }}
      >
        {items.map((item) => {
          return (
            <Box key={item.key}>
              <Typography
                color="text.secondary"
                sx={{ fontWeight: 700, mb: 0.5 }}
                variant="body2"
              >
                {item.label}
              </Typography>
              {item.kind === "relationship" ? (
                <RelatedRecordDialogLink
                  parentRecord={record}
                  relationship={item.relationship}
                  surface="summary"
                />
              ) : (
                <Typography variant="body1">
                  {formatScalarValue(record[item.attribute.name], item.attribute.kind)}
                </Typography>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}

function isBackReferenceItem(
  item: DisplayItem,
  relationship: ResourceRelationshipMeta,
  parentResource: string,
): boolean {
  if (item.kind === "attribute") {
    return relationship.fks.includes(item.attribute.name);
  }

  return (
    item.relationship.targetResource === parentResource
    && item.relationship.fks.some((fk) => relationship.fks.includes(fk))
  );
}

function RelationshipTabRowActions({
  relationshipName,
}: {
  relationshipName: string;
}) {
  const record = useRecordContext<Record<string, unknown>>();

  if (!record?.id) {
    return null;
  }

  const stopRowNavigation = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  return (
    <Box
      data-testid={`relationship-row-actions:${relationshipName}:${String(record.id)}`}
      onClick={stopRowNavigation}
      onMouseDown={stopRowNavigation}
      sx={{ alignItems: "center", display: "flex", gap: 1 }}
    >
      <EditButton
        aria-label={`Edit related ${relationshipName}`}
        data-testid={`relationship-row-action:edit:${relationshipName}:${String(record.id)}`}
        label=""
        onClick={stopRowNavigation}
        sx={{ minWidth: 0, px: 0.5 }}
      />
      <DeleteWithConfirmButton
        aria-label={`Delete related ${relationshipName}`}
        confirmContent="Delete this related record?"
        confirmTitle="Delete related record?"
        data-testid={`relationship-row-action:delete:${relationshipName}:${String(record.id)}`}
        label=""
        mutationMode="pessimistic"
        onClick={stopRowNavigation}
        sx={{ minWidth: 0, px: 0.5 }}
      />
    </Box>
  );
}

export function ManyRelationshipTab({
  parentResource,
  relationship,
}: {
  parentResource: string;
  relationship: ResourceRelationshipMeta;
}) {
  const dataProvider = useDataProvider() as SafrsDataProvider;
  const record = useRecordContext<Record<string, unknown>>();
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const targetMeta = useMemo(
    () => buildResourceMeta(schema, rawYaml, relationship.targetResource),
    [rawYaml, relationship.targetResource, schema],
  );
  const items = useMemo(
    () =>
      visibleDisplayItems(targetMeta, "list")
        .filter((item) => !isBackReferenceItem(item, relationship, parentResource))
        .slice(0, 8),
    [parentResource, relationship, targetMeta],
  );
  const sortField = targetMeta.userKey ?? targetMeta.attributes[0]?.name ?? "id";
  const parentId = record?.id;
  const executeRequest = useMemo(
    () => resolveRelationshipExecuteRequest(schema, relationship, parentId as string | number | undefined),
    [parentId, relationship, schema],
  );
  const embeddedRows = useMemo(
    () => (record ? getRecordRelationValues(record, relationship.name) : []),
    [record, relationship.name],
  );
  const [rows, setRows] = useState<Record<string, unknown>[]>(
    () => sortRelatedRecords(embeddedRows, sortField),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadSource, setLoadSource] = useState<RelationshipLoadSource>(
    embeddedRows.length > 0 ? "embedded" : "unresolved",
  );
  const unresolvedReason = executeRequest.kind === "unresolved"
    ? executeRequest.reason
    : null;

  useEffect(() => {
    if (embeddedRows.length > 0) {
      setRows(sortRelatedRecords(embeddedRows, sortField));
      setLoading(false);
      setError(null);
      setLoadSource("embedded");
      return;
    }

    if (executeRequest.kind === "unresolved") {
      setRows([]);
      setLoading(false);
      setError(null);
      setLoadSource("unresolved");
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        const routeResult = await dataProvider.execute<Record<string, unknown> | Record<string, unknown>[]>(
          executeRequest.value.resource,
          {
            action: executeRequest.value.action,
            id: executeRequest.value.id,
            method: "GET",
          },
        );
        if (!cancelled) {
          setRows(sortRelatedRecords(extractExecuteRecords(routeResult.data), sortField));
          setLoading(false);
          setLoadSource("relationship-route");
        }
      } catch (nextError: unknown) {
        if (!cancelled) {
          setRows([]);
          setLoading(false);
          setError(nextError instanceof Error ? nextError.message : String(nextError));
          setLoadSource("error");
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [dataProvider, embeddedRows, executeRequest, parentId, sortField]);

  const listContext = useList<Record<string, unknown>>({
    data: rows,
    isPending: loading,
    page: 1,
    perPage: DEFAULT_PAGE_SIZE,
    resource: relationship.targetResource,
    sort: { field: sortField, order: "ASC" },
  });

  if (loading) {
    return (
      <Box
        data-testid={`relationship-tab-panel:tomany:${relationship.name}`}
        data-relationship-direction="tomany"
        data-relationship-fetch-source={loadSource}
        data-relationship-route-path={executeRequest.kind === "resolved" ? executeRequest.value.routePath : ""}
      >
        <Loading />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        data-testid={`relationship-tab-panel:tomany:${relationship.name}`}
        data-relationship-direction="tomany"
        data-relationship-fetch-source={loadSource}
        data-relationship-route-path={executeRequest.kind === "resolved" ? executeRequest.value.routePath : ""}
      >
        <Typography color="error" sx={{ pt: 2 }}>
          {error}
        </Typography>
      </Box>
    );
  }

  if (rows.length === 0) {
    return (
      <Box
        data-testid={`relationship-tab-panel:tomany:${relationship.name}`}
        data-relationship-direction="tomany"
        data-relationship-fetch-source={loadSource}
        data-relationship-route-path={executeRequest.kind === "resolved" ? executeRequest.value.routePath : ""}
      >
        {loadSource === "unresolved" && unresolvedReason ? (
          <RelationshipResolutionAlert
            direction="tomany"
            reason={unresolvedReason}
            relationship={relationship}
          />
        ) : (
          <Typography color="text.secondary" sx={{ pt: 2 }}>
            No related records.
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Box
      data-testid={`relationship-tab-panel:tomany:${relationship.name}`}
      data-relationship-direction="tomany"
      data-relationship-fetch-source={loadSource}
      data-relationship-route-path={executeRequest.kind === "resolved" ? executeRequest.value.routePath : ""}
    >
      <ListContextProvider value={listContext}>
        <Datagrid bulkActionButtons={false} rowClick="show">
          {items.map((item) => renderListField(item, schema))}
          <FunctionField
            key={`relationship-row-actions:${relationship.name}`}
            label=""
            render={() => <RelationshipTabRowActions relationshipName={relationship.name} />}
          />
        </Datagrid>
      </ListContextProvider>
    </Box>
  );
}

function TabPanel({
  children,
  index,
  value,
}: {
  children: ReactNode;
  index: number;
  value: number;
}) {
  return (
    <Box hidden={value !== index} sx={{ pt: 3 }}>
      {value === index ? children : null}
    </Box>
  );
}

function ShowContent({
  resource,
}: {
  resource: string;
}) {
  const resourceMeta = useResourceMeta(resource);
  const overviewItems = useMemo(
    () => visibleDisplayItems(resourceMeta, "show"),
    [resourceMeta],
  );
  const relationships = useMemo(
    () =>
      resourceMeta.relationships.filter(
        (relationship) => !isRelationshipHidden(relationship, "show"),
      ),
    [resourceMeta.relationships],
  );
  const preferredTabIndex = useMemo(
    () => getDefaultRelationshipTabIndex(relationships, resource),
    [relationships, resource],
  );
  const [tabIndex, setTabIndex] = useState(preferredTabIndex);

  useEffect(() => {
    setTabIndex(preferredTabIndex);
  }, [preferredTabIndex, resource]);

  return (
    <Box>
      <OverviewGrid items={overviewItems} resourceMeta={resourceMeta} />
      {relationships.length > 0 ? (
        <>
          <Divider sx={{ my: 4 }} />
          <Tabs
            allowScrollButtonsMobile
            onChange={(_event, nextIndex) => setTabIndex(nextIndex)}
            scrollButtons="auto"
            value={tabIndex}
            variant="scrollable"
          >
            {relationships.map((relationship) => (
              <Tab key={relationship.name} label={relationship.label} />
            ))}
          </Tabs>
          {relationships.map((relationship, index) => (
            <TabPanel index={index} key={relationship.name} value={tabIndex}>
              {relationship.direction === "tomany" ? (
                <ManyRelationshipTab
                  parentResource={resource}
                  relationship={relationship}
                />
              ) : (
                <SingleRelationshipTab relationship={relationship} />
              )}
            </TabPanel>
          ))}
        </>
      ) : null}
    </Box>
  );
}

function SchemaDrivenList({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const resourceMeta = useResourceMeta(resource);
  const displayItems = visibleDisplayItems(resourceMeta, "list");
  const filters = resourceMeta.searchColumns.length > 0
    ? [
        <SearchInput
          alwaysOn
          key="q"
          placeholder={buildSearchPlaceholder(resourceMeta)}
          source="q"
        />,
      ]
    : undefined;

  return (
    <List filters={filters} perPage={DEFAULT_PAGE_SIZE}>
      <Datagrid rowClick="show">
        {displayItems.map((item) => renderListField(item, schema))}
      </Datagrid>
    </List>
  );
}

function SchemaDrivenShow({ resource }: { resource: string }) {
  return (
    <Show>
      <ShowContent resource={resource} />
    </Show>
  );
}

function SchemaDrivenEdit({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const attributes = visibleAttributes(resourceMeta, "edit").filter(
    (attribute) => !attribute.isPrimaryKey,
  );

  return (
    <Edit>
      <SimpleForm>
        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: {
              xs: "minmax(0, 1fr)",
              md: "repeat(12, minmax(0, 1fr))",
            },
          }}
        >
          {attributes.map((attribute) => renderFormItem(attribute, schema, rawYaml))}
        </Box>
      </SimpleForm>
    </Edit>
  );
}

function SchemaDrivenCreate({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const attributes = visibleAttributes(resourceMeta, "create").filter(
    (attribute) => !attribute.isPrimaryKey,
  );

  return (
    <Create>
      <SimpleForm>
        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: {
              xs: "minmax(0, 1fr)",
              md: "repeat(12, minmax(0, 1fr))",
            },
          }}
        >
          {attributes.map((attribute) => renderFormItem(attribute, schema, rawYaml))}
        </Box>
      </SimpleForm>
    </Create>
  );
}

function isResourceHidden(resourceMeta: ResourceMeta): boolean {
  return resourceMeta.hidden === true || resourceMeta.hidden === "true";
}

export function buildResources(
  resources: ResourcePages[],
  schema: Schema,
  rawYaml: RawAdminYaml,
): ReactNode[] {
  return resources
    .map((resource, index) => ({
      index,
      resource,
      resourceMeta: buildResourceMeta(schema, rawYaml, resource.name),
    }))
    .filter(({ resourceMeta }) => !isResourceHidden(resourceMeta))
    .sort((left, right) => {
      const leftOrder = left.resourceMeta.menuOrder;
      const rightOrder = right.resourceMeta.menuOrder;

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
    .map(({ resource, resourceMeta }) => (
      <Resource
        key={resource.name}
        create={resource.create}
        edit={resource.edit}
        list={resource.list}
        name={resource.name}
        options={{ label: resourceMeta.label }}
        recordRepresentation={resource.recordRepresentation ?? resourceMeta.userKey ?? "id"}
        show={resource.show}
      />
    ));
}
```

Required relationship behavior:

- this file MUST import and use the helpers from `relationshipUi.tsx`
- this file MUST render a metadata-driven relationship-tab show page, not a
  plain single-layout show renderer with deferred follow-up notes
- generated list pages MUST render `toone` foreign-key-backed columns through
  `RelatedRecordDialogLink`, not raw scalar ids
- generated show-page overview summaries MUST also render `toone`
  relationship items through `RelatedRecordDialogLink`, not plain text labels
- generated relationship tabs SHOULD expose stable `data-testid` and
  `data-relationship-fetch-source` markers so the generic Playwright smoke can
  prove canonical relationship behavior without hardcoding one domain model
- FK-backed scalar attributes that carry `attribute.relationship` metadata
  SHOULD be collapsed into one relationship display item so duplicate raw-FK
  columns are suppressed
- generated show pages MUST render:
  - `tomany` relationships as datagrid tabs
  - `toone` relationships as summary tabs
