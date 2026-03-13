# Query Contract

This file defines the subset of SAFRS query behavior that the generated
frontend runtime and data provider rely on.

The concrete endpoint examples below use the starter `Item` resource. They are
worked examples, not a claim that every app will expose `/api/items`.

## Supported query features

Generated collection endpoints MUST support:

- pagination
- sorting
- include
- SAFRS filtering

## Pagination

The backend MUST support:

- `page[number]`
- `page[size]`

Example:

```text
/api/items?page[number]=1&page[size]=25
```

## Sorting

The backend MUST support:

- `sort=<field>`
- `sort=-<field>` for descending

Example:

```text
/api/items?sort=title
```

## Include

The backend MUST support:

- `include=collection,status`

Example:

```text
/api/items?include=collection,status
```

Relationship names in `include` MUST match ORM relationship names exactly.

## Filtering

Supported SAFRS modes:

1. attribute filters

```text
/api/items?filter[status_id]=1
```

2. JSON filter payload

```text
/api/items?filter={"name":"title","op":"ilike","val":"%board%"}
```

3. grouped boolean filtering

```text
/api/items?filter={"or":[{"name":"title","op":"ilike","val":"%board%"},{"name":"title","op":"ilike","val":"%check%"}]}
```

## Search contract

Fields marked `search: true` in `admin.yaml` are the fields the frontend should
search across.

The backend search behavior is implemented through SAFRS grouped filters using
`filter={"or":[...]}`

Search semantics:

- partial string matching on text fields
- `ilike`-style behavior in the starter runtime
- OR across all search-enabled fields
- if other filters are present, search composes with them under an AND-style
  grouped SAFRS filter

The starter frontend/runtime contract only treats `text` fields as searchable
in v1. Numeric and datetime search require an explicit project-specific search
strategy.

The frontend MUST NOT assume an extra ad hoc `/search` endpoint.

## Validation behavior

Invalid filters MUST return a JSON:API validation error.

The runtime implementation that emits grouped search filters is part of the
archive under:

- `templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md`

Actual collection paths must be validated against the running SAFRS backend and
the generated `admin.yaml`.
