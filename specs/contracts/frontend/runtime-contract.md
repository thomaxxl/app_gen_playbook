# Frontend Runtime Contract

This file defines the actual shared-runtime contract that generated frontends
MUST follow.

The generated frontend MUST NOT depend on hidden behavior outside this
contract.

The frontend MUST NOT introduce domain validation or workflow behavior that is
absent from `../../runs/current/artifacts/product/business-rules.md`. It MAY
mirror only the subset of approved rules whose `Frontend Mirror` field is not
`none`.

## Archive-contained runtime files

The starter archive MUST ship these runtime snippets:

- `templates/app/frontend/theme.ts.md`
- `templates/app/frontend/PageHeader.tsx.md`
- `templates/app/frontend/EmptyState.tsx.md`
- `templates/app/frontend/ErrorState.tsx.md`
- `templates/app/frontend/FormSection.tsx.md`
- `templates/app/frontend/SummaryCard.tsx.md`
- `templates/app/frontend/SchemaDrivenAdminApp.tsx.md`
- `templates/app/frontend/shared-runtime/resourceRegistry.tsx.md`
- `templates/app/frontend/shared-runtime/relationshipUi.tsx.md`
- `templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md`
- `templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md`
- `templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
- `templates/app/frontend/shared-runtime/files/uploadAwareDataProvider.ts.md`
- `templates/app/frontend/shared-runtime/files/fileValueAdapters.ts.md`
- `templates/app/frontend/shared-runtime/files/fileFieldHelpers.ts.md`

The starter frontend scaffold MUST also ship:

- `templates/app/frontend/index.html.md`
- `templates/app/frontend/Home.tsx.md`
- `templates/app/frontend/theme.ts.md`
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
10. honor runtime-consumed form layout metadata such as textarea rows and form
    width overrides
11. render a visible loading state while bootstrapping
12. render a visible full-page error state on fetch/parse/provider failure
13. catch render-time metadata failures such as bad resource names or bad
    reference targets with a visible error boundary
14. render `<Admin dataProvider={...} title={...}>`
15. render `children` first
16. render explicit resource elements from the `resourcePages` prop as direct
    `Admin` children
17. render generated relationships using the relationship contract in
    `relationship-ui.md`
18. expose consistent page-shell primitives for title, purpose text, empty
    states, and error states
19. preserve a shared theme baseline across Home and custom pages

The runtime MUST preserve raw `admin.yaml tab_groups` through the adapter
layer and MUST remain functional when `schema.resources[...].relationships` is
partial. The runtime MUST combine:

- normalized schema relationship metadata
- `schema.fkToRelationship`
- raw `admin.yaml`

instead of assuming the normalized relationship graph is complete.

That `children` slot is the official extension point for:

- direct custom `Resource` elements such as the required `Home` page
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

## Required Home page integration

Every generated app MUST add a direct `Resource` child for the `Home` page.

That `Resource` MUST:

- use the name `Home`
- include a visible Home icon
- produce a left-sidebar entry labeled `Home`
- route to the `Home.tsx` page component

The `Home` page MUST be treated as a project page, not as a backend resource
declared in `admin.yaml`.

The `Home` page MUST provide:

- a visible title
- a short basic description or purpose text
- a visible path into the main app flow

## Required starter UI primitives

The generated frontend MUST ship starter UI primitives for:

- page headers
- empty states
- error states
- form sections
- summary cards

Those primitives MUST be usable by:

- `Home.tsx`
- starter or non-starter custom pages
- bootstrap and render-failure screens where appropriate

The generated frontend SHOULD apply an app-local theme and CSS baseline from
`frontend/src/theme.ts` and `frontend/src/main.tsx`.

## Required relationship behavior

The shared runtime MUST implement the relationship UI contract in
`relationship-ui.md`.

Relationship tabs and related-record dialogs are baseline runtime behavior for
generated apps. The runtime MUST ship and wire this behavior unless the run
explicitly documents a different UX decision in its run-owned artifacts.

At minimum, the runtime MUST:

- replace visible `toone` foreign-key columns with readable relationship
  display items in generated list/show views
- resolve readable relationship labels using embedded related objects when
  available and foreign-key fallback values when not
- provide a related-record dialog with `EDIT` and `VIEW` actions
- render `tomany` show-page tabs as datagrids
- render `toone` show-page tabs as summary panels
- keep generated forms bound to scalar foreign-key inputs
- attach resolved `toone` relationships to FK attributes so generated
  list/show views can replace raw FK columns with relationship display items
- expose relationship ordering and lookup metadata through `ResourceMeta`
  instead of rebuilding that logic independently in each page component

The runtime MUST NOT rely on raw-id-only rendering for generated relationship
columns when relationship metadata is available.

## Required form layout behavior

Generated create/edit forms MUST use responsive layout heuristics rather than
rendering every field full-width in a single vertical stack.

At minimum, the runtime MUST:

- default standard fields to one-third desktop width
- allow three standard fields on the same row at desktop sizes
- apply narrower widths to compact scalar fields when the field shape suggests
  it
- default multiline textarea-style fields to full width
- default upload/file/image inputs to full width
- honor explicit form-width overrides from runtime metadata
- honor explicit textarea row hints from runtime metadata

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

The adapter MUST NOT drop `tab_groups` or other runtime-consumed relationship
inputs during normalization preparation.

Upload segmentation note:

- the starter shared runtime MAY ship baseline no-op upload helpers
- that baseline footprint is an implementation convenience, not feature
  enablement
- the uploads feature remains disabled unless the run capability profile
  enables it and the uploads feature pack is loaded

## File-upload extension

If the app includes upload-backed fields, the frontend runtime MUST add an
upload-aware data-provider wrapper above the normal SAFRS provider path.

Required behavior:

1. start from the normal SAFRS base provider
2. apply the search-enabled wrapper
3. apply the upload-aware wrapper

The upload-aware wrapper MUST:

- intercept `create` and `update`
- detect values containing `rawFile`
- create pending file metadata through SAFRS
- upload bytes through the dedicated multipart endpoint
- replace temporary form values with stable file metadata or file-id payloads
- apply upload-field mapping per resource, not through one global flat field
  map

If the app declares upload fields in `admin.yaml`, the runtime SHOULD derive
the upload mapping from raw `admin.yaml` metadata instead of forcing each app
to hand-code a separate provider map.

The runtime MUST NOT push raw `File` objects into the normal SAFRS JSON:API
provider path.

## Required normalized schema surface

The starter runtime depends on this explicit normalized schema surface from
`safrs-jsonapi-client`:

- `schema.resources[resource].attributeConfigs`
- `schema.resources[resource].relationships`
- `schema.resources[resource].searchCols`
- `schema.resources[resource].userKey`
- `schema.fkToRelationship`
- `schema.resourceByType`
- `schema.delimiter`

No other normalized schema internals are part of the contract.

## Shim contract

The canonical browser shim path is:

- `frontend/src/shims/fs-promises.ts`

The Vite alias MUST point to that file.

The implementation MUST NOT define a second competing shim path under
`shared-runtime/`.
