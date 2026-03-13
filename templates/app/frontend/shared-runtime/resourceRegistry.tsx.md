# `frontend/src/shared-runtime/resourceRegistry.tsx`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../specs/contracts/frontend/admin-yaml-contract.md)

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
  List,
  NumberField,
  NumberInput,
  ReferenceField,
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
  type ResourceMeta,
  useResourceMeta,
} from "./admin/resourceMetadata";

const DEFAULT_PAGE_SIZE = 25;

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
  attribute: ResourceAttributeMeta,
  schema: ReturnType<typeof useAdminSchema>,
  rawYaml: RawAdminYaml,
) {
  if (attribute.kind === "reference" && attribute.reference) {
    const targetMeta = buildResourceMeta(schema, rawYaml, attribute.reference);
    return (
      <ReferenceField
        key={attribute.name}
        label={attribute.label}
        reference={attribute.reference}
        source={attribute.name}
      >
        <TextField source={targetMeta.userKey ?? "id"} />
      </ReferenceField>
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

  return <TextInput {...commonProps} />;
}

function SchemaDrivenList({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const attributes = visibleAttributes(resourceMeta, "list");
  const filters = resourceMeta.searchColumns.length > 0
    ? [<SearchInput alwaysOn key="q" placeholder={buildSearchPlaceholder(resourceMeta)} source="q" />]
    : undefined;

  return (
    <List filters={filters} perPage={DEFAULT_PAGE_SIZE}>
      <Datagrid rowClick="show">
        {attributes.map((attribute) => renderField(attribute, schema, rawYaml))}
      </Datagrid>
    </List>
  );
}

function SchemaDrivenShow({ resource }: { resource: string }) {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();
  const resourceMeta = useResourceMeta(resource);
  const attributes = visibleAttributes(resourceMeta, "show");

  return (
    <Show>
      <SimpleShowLayout>
        {attributes.map((attribute) => renderField(attribute, schema, rawYaml))}
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
