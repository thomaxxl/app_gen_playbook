# `frontend/src/shared-runtime/resourceRegistry.tsx`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../specs/contracts/frontend/admin-yaml-contract.md)
- [../../../../specs/contracts/frontend/relationship-ui.md](../../../../specs/contracts/frontend/relationship-ui.md)
- [relationshipUi.tsx.md](relationshipUi.tsx.md)

```tsx
import type { ReactElement, ReactNode } from "react";
import type { Schema } from "safrs-jsonapi-client";
import {
  AutocompleteInput,
  BooleanField,
  BooleanInput,
  Create,
  Datagrid,
  DateField,
  DateInput,
  Edit,
  FileField,
  FileInput,
  ImageField,
  ImageInput,
  List,
  NumberField,
  NumberInput,
  ReferenceInput,
  Resource,
  SearchInput,
  Show,
  SimpleForm,
  SimpleShowLayout,
  TextField,
  TextInput,
} from "react-admin";

import { useAdminSchema, useRawAdminYaml } from "./admin/schemaContext";
import {
  buildResourceMeta,
  type RawAdminYaml,
  type ResourceAttributeMeta,
  type ResourceRelationshipMeta,
  type ResourceMeta,
  useResourceMeta,
} from "./admin/resourceMetadata";
import { RelatedRecordDialogLink } from "./relationshipUi";

const DEFAULT_PAGE_SIZE = 25;

export interface ResourcePages {
  name: string;
  list: () => ReactElement;
  create: () => ReactElement;
  edit: () => ReactElement;
  show: () => ReactElement;
  recordRepresentation?: string;
}

type DisplayItem =
  | { kind: "attribute"; attribute: ResourceAttributeMeta }
  | { kind: "relationship"; relationship: ResourceRelationshipMeta };

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

function isHidden(attribute: ResourceAttributeMeta, mode: "list" | "show" | "create" | "edit"): boolean {
  const explicitVisibility = (
    mode === "list"
      ? attribute.list
      : mode === "show"
        ? attribute.show
        : mode === "create"
          ? attribute.create
          : attribute.edit
  );

  if (explicitVisibility === true) {
    return false;
  }

  if (explicitVisibility === false) {
    return true;
  }

  if (attribute.hidden === true || attribute.hidden === "true") {
    return true;
  }

  return false;
}

function visibleAttributes(resourceMeta: ResourceMeta, mode: "list" | "show" | "create" | "edit") {
  return resourceMeta.attributes
    .filter((attribute) => !isHidden(attribute, mode))
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

function visibleDisplayItems(resourceMeta: ResourceMeta, mode: "list" | "show"): DisplayItem[] {
  const items: DisplayItem[] = [];
  const emittedRelationships = new Set<string>();

  for (const attribute of visibleAttributes(resourceMeta, mode)) {
    if (attribute.relationship && !emittedRelationships.has(attribute.relationship.name)) {
      items.push({ kind: "relationship", relationship: attribute.relationship });
      emittedRelationships.add(attribute.relationship.name);
      continue;
    }

    items.push({ kind: "attribute", attribute });
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

function renderField(
  item: DisplayItem,
  schema: ReturnType<typeof useAdminSchema>,
  rawYaml: RawAdminYaml,
) {
  if (item.kind === "relationship") {
    return (
      <RelatedRecordDialogLink
        key={`relationship:${item.relationship.name}`}
        relationship={item.relationship}
      />
    );
  }

  const { attribute } = item;

  if (attribute.kind === "reference" && attribute.reference) {
    return (
      <TextField
        key={attribute.name}
        label={attribute.label}
        source={attribute.name}
      />
    );
  }

  if (attribute.kind === "number") {
    return <NumberField key={attribute.name} label={attribute.label} source={attribute.name} />;
  }

  if (attribute.kind === "boolean") {
    return <BooleanField key={attribute.name} label={attribute.label} source={attribute.name} />;
  }

  if (attribute.kind === "date") {
    return <DateField key={attribute.name} label={attribute.label} source={attribute.name} />;
  }

  if (attribute.kind === "image") {
    return (
      <ImageField
        key={attribute.name}
        label={attribute.label}
        source={`${attribute.name}.src`}
        title={`${attribute.name}.title`}
      />
    );
  }

  if (attribute.kind === "file") {
    return (
      <FileField
        key={attribute.name}
        label={attribute.label}
        source={`${attribute.name}.src`}
        title={`${attribute.name}.title`}
      />
    );
  }

  return <TextField key={attribute.name} label={attribute.label} source={attribute.name} />;
}

function renderInput(
  attribute: ResourceAttributeMeta,
  schema: ReturnType<typeof useAdminSchema>,
  rawYaml: RawAdminYaml,
) {
  if (attribute.readonly) {
    return null;
  }

  if (attribute.kind === "reference" && attribute.reference) {
    const targetMeta = buildResourceMeta(schema, rawYaml, attribute.reference);
    return (
      <ReferenceInput
        key={attribute.name}
        label={attribute.label}
        reference={attribute.reference}
        source={attribute.name}
      >
        <AutocompleteInput optionText={targetMeta.userKey ?? "id"} />
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

  if (attribute.kind === "image") {
    return (
      <ImageInput
        {...commonProps}
        accept={attribute.accept ?? "image/*"}
      >
        <ImageField source="src" title="title" />
      </ImageInput>
    );
  }

  if (attribute.kind === "file") {
    return (
      <FileInput {...commonProps} accept={attribute.accept}>
        <FileField source="src" title="title" />
      </FileInput>
    );
  }

  return <TextInput {...commonProps} />;
}

function SchemaDrivenList({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const displayItems = visibleDisplayItems(resourceMeta, "list");
  const filters = resourceMeta.searchColumns.length > 0
    ? [<SearchInput alwaysOn key="q" placeholder={buildSearchPlaceholder(resourceMeta)} source="q" />]
    : undefined;

  return (
    <List filters={filters} perPage={DEFAULT_PAGE_SIZE}>
      <Datagrid rowClick="show">
        {displayItems.map((item) => renderField(item, schema, rawYaml))}
      </Datagrid>
    </List>
  );
}

function SchemaDrivenShow({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const displayItems = visibleDisplayItems(resourceMeta, "show");

  return (
    <Show>
      <SimpleShowLayout>
        {displayItems.map((item) => renderField(item, schema, rawYaml))}
      </SimpleShowLayout>
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
        {attributes.map((attribute) => renderInput(attribute, schema, rawYaml))}
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
        {attributes.map((attribute) => renderInput(attribute, schema, rawYaml))}
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

Required relationship extension:

- this file MUST import and use the helpers from `relationshipUi.tsx`
- this file SHOULD use an explicit display-item model such as:
  - scalar attribute display items
  - relationship display items
- generated list pages MUST render `toone` foreign-key-backed columns through
  `RelatedRecordDialogLink`, not raw scalar ids
- FK-backed scalar attributes that carry `attribute.relationship` metadata
  SHOULD be collapsed into one relationship display item so duplicate raw-FK
  columns are suppressed
- generated show pages MUST render:
  - `tomany` relationships as datagrid tabs
  - `toone` relationships as summary tabs
- the relationship tab default MUST use the priority order defined in
  `specs/contracts/frontend/relationship-ui.md`
- relationship tab ordering SHOULD use:
  - `tab_groups` order first
  - schema-discovered extra relationships appended afterward
- generated forms MUST keep scalar foreign-key inputs even though list/show
  rendering uses relationship-aware helpers
