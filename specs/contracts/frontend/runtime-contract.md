# Frontend Runtime Contract

This file defines the actual shared-runtime contract that generated frontends
MUST follow.

The generated frontend MUST NOT depend on hidden behavior outside this
contract.

## Archive-contained runtime files

The starter archive MUST ship these runtime snippets:

- `templates/app/frontend/SchemaDrivenAdminApp.tsx.md`
- `templates/app/frontend/shared-runtime/resourceRegistry.tsx.md`
- `templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md`
- `templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md`
- `templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md`

The starter frontend scaffold MUST also ship:

- `templates/app/frontend/index.html.md`
- `templates/app/frontend/tsconfig.json.md`
- `templates/app/frontend/tsconfig.app.json.md`
- `templates/app/frontend/tsconfig.node.json.md`
- `templates/app/frontend/vite-env.d.ts.md`

## Runtime entrypoint

`SchemaDrivenAdminApp` is the app-level wrapper around:

- `admin.yaml` loading
- adapter translation from playbook `admin.yaml` shape to the current
  `safrs-jsonapi-client` normalizer shape
- raw `admin.yaml` retention for local metadata lookups
- schema context
- data-provider creation
- explicit `Resource` registration
- optional custom routes

Required props:

```ts
type ResourcePages = {
  name: string;
  list: ComponentType;
  create: ComponentType;
  edit: ComponentType;
  show: ComponentType;
  recordRepresentation?: string;
};

type SchemaDrivenAdminAppProps = {
  appConfig: {
    adminYamlUrl: string;
    apiRoot: string;
    title: string;
  };
  resourcePages: ResourcePages[];
  children?: ReactNode;
};
```

## Required behavior

`SchemaDrivenAdminApp` MUST:

1. load `admin.yaml`
2. keep the parsed raw YAML available to the local runtime
3. adapt the raw YAML to the client normalizer input shape
4. normalize the adapted document through `safrs-jsonapi-client`
5. create the base data provider
6. wrap it with the search-enabled provider
7. make search requests use the explicit `admin.yaml endpoint` mapping
8. honor runtime-consumed resource metadata for label, hidden, and menu order
9. honor runtime-consumed field ordering metadata
10. render a visible loading state while bootstrapping
11. render a visible full-page error state on fetch/parse/provider failure
12. catch render-time metadata failures such as bad resource names or bad
    reference targets with a visible error boundary
13. render `<Admin dataProvider={...} title={...}>`
14. render `children` first
15. render explicit resource elements from the `resourcePages` prop as direct
    `Admin` children

That `children` slot is the official extension point for:

- `CustomRoutes noLayout`
- custom landing pages
- extra dashboard routes

It MUST NOT be left implicit.

The render-time boundary MUST wrap a child component that performs resource
registration. The implementation MUST NOT evaluate `buildResources(...)`
outside the boundary and then expect the boundary to catch those failures.

## Resource registration

The frontend MUST NOT auto-discover resources.

It MUST explicitly import a `resourcePages` registry and pass it into
`SchemaDrivenAdminApp`.

Required shape:

```ts
export const resourcePages: ResourcePages[] = [
  CollectionPages,
  ItemPages,
  StatusPages,
];
```

That array is a starter example only. For a non-starter domain, the
implementation MUST register one entry per resource declared in
`../../architecture/resource-naming.md`.

Each `ResourcePages` entry MUST be turned into a React-admin `<Resource>` by
the shared runtime. Hidden auto-discovery is NOT allowed.

The runtime MUST NOT hide generated `<Resource>` elements behind a nested
wrapper component that React-Admin cannot introspect. `Admin` route
registration depends on direct child elements at render time.

## YAML parsing

The frontend runtime relies on `safrs-jsonapi-client` for:

- normalizing adapted schema metadata
- creating the base React-Admin data provider

The runtime still owns:

- the adapter that translates playbook `admin.yaml` shape into the client
  normalizer shape
- retaining the raw parsed YAML next to the normalized schema
- search wrapping
- resource wiring
- frontend-visible bootstrap/error handling

The runtime contract MUST NOT depend on an undocumented `schema.raw` field.
If the runtime needs raw `admin.yaml` metadata for labels, ordering, or
visibility, it must carry that raw YAML in local app state explicitly.

## Required normalized schema surface

The starter runtime depends on this explicit normalized schema surface from
`safrs-jsonapi-client`:

- `schema.resources[resource].attributeConfigs`
- `schema.resources[resource].searchCols`
- `schema.resources[resource].userKey`
- `schema.resourceByType`
- `schema.delimiter`

No other normalized schema internals are part of the contract.

## Shim contract

The canonical browser shim path is:

- `frontend/src/shims/fs-promises.ts`

The Vite alias MUST point to that file.

The implementation MUST NOT define a second competing shim path under
`shared-runtime/`.
