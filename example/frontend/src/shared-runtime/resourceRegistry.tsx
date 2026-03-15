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
  Edit,
  FunctionField,
  List,
  Loading,
  NumberField,
  NumberInput,
  ReferenceInput,
  ReferenceManyField,
  Resource,
  SearchInput,
  Show,
  SimpleForm,
  TextField,
  TextInput,
  useRecordContext,
} from "react-admin";
import type { Schema } from "safrs-jsonapi-client";

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
  getDefaultRelationshipTabIndex,
  getRelatedRecordLabel,
  RelatedRecordDialogLink,
  SingleRelationshipTab,
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
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
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
          let value = "-";

          if (item.kind === "relationship") {
            const targetMeta = buildResourceMeta(
              schema,
              rawYaml,
              item.relationship.targetResource,
            );
            value = getRelatedRecordLabel(record, item.relationship, targetMeta);
          } else {
            value = formatScalarValue(record[item.attribute.name], item.attribute.kind);
          }

          return (
            <Box key={item.key}>
              <Typography
                color="text.secondary"
                sx={{ fontWeight: 700, mb: 0.5 }}
                variant="body2"
              >
                {item.label}
              </Typography>
              <Typography variant="body1">{value}</Typography>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}

function buildRelationshipTarget(
  relationship: ResourceRelationshipMeta,
  delimiter: string,
): string {
  return relationship.fks.length === 1
    ? relationship.fks[0]
    : relationship.fks.join(relationship.compositeDelimiter ?? delimiter);
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

function ManyRelationshipTab({
  parentResource,
  relationship,
}: {
  parentResource: string;
  relationship: ResourceRelationshipMeta;
}) {
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
        .slice(0, targetMeta.maxListColumns),
    [parentResource, relationship, targetMeta],
  );
  const target = buildRelationshipTarget(relationship, schema.delimiter);
  const sortField = targetMeta.userKey ?? targetMeta.attributes[0]?.name ?? "id";

  return (
    <ReferenceManyField
      perPage={DEFAULT_PAGE_SIZE}
      reference={relationship.targetResource}
      sort={{ field: sortField, order: "ASC" }}
      target={target}
    >
      <Datagrid bulkActionButtons={false} rowClick="show">
        {items.map((item) => renderListField(item, schema))}
      </Datagrid>
    </ReferenceManyField>
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
