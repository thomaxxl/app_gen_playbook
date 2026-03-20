# `app/reference/admin.yaml`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

When this file is derived from backend discovery or OpenAPI-shaped input, the
preferred playbook lane is the Codex `openapi-to-admin-yaml` skill. Treat
manual editing as the refinement step after generation, not the default first
step. The default generation input is the live `/jsonapi.json` served by the
running FastAPI backend.

Starter example shape:

```yaml
resources:
  Collection:
    endpoint: /api/collections
    label: Collections
    user_key: name
    menu_order: 10
    attributes:
      id:
        type: number
        readonly: true
        hidden: true
      name:
        type: text
        label: Collection Name
        required: true
        search: true
        order: 10
        list: true
        show: true
        create: true
        edit: true
      item_count:
        type: number
        label: Item Count
        readonly: true
        hidden: true
      total_estimate_hours:
        type: number
        label: Total Estimate Hours
        readonly: true
        hidden: true
    tab_groups:
      default:
        label: Related
        relationships:
          - items

  Item:
    endpoint: /api/items
    label: Items
    user_key: title
    menu_order: 20
    attributes:
      id:
        type: number
        readonly: true
        hidden: true
      title:
        type: text
        required: true
        search: true
      estimate_hours:
        type: number
        label: Estimate Hours
        required: true
        list: true
        show: true
        create: true
        edit: true
      completed_at:
        type: datetime
        label: Completed At
        list: false
        show: true
        create: true
        edit: true
      collection_id:
        type: reference
        label: Collection
        reference: Collection
        required: true
        list: true
        show: true
        create: true
        edit: true
      status_id:
        type: reference
        label: Status
        reference: Status
        required: true
        list: true
        show: true
        create: true
        edit: true
      status_code:
        type: text
        label: Status Code
        readonly: true
        hidden: true
      is_completed:
        type: boolean
        label: Completed
        readonly: true
        hidden: true

  Status:
    endpoint: /api/statuses
    label: Statuses
    user_key: label
    menu_order: 30
    attributes:
      id:
        type: number
        readonly: true
        hidden: true
      code:
        type: text
        label: Code
        required: true
        search: true
      label:
        type: text
        label: Label
        required: true
        search: true
      is_closed:
        type: boolean
        label: Closed
```

Notes:

- `user_key` is what the frontend should use for clickable foreign-key labels.
- `endpoint` is required. Do not rely on hidden resource-name to API-path
  conversion.
- the concrete endpoint values shown here are starter-example values and must be
  validated against actual SAFRS output for the generated app
- `search: true` is the source of list-search fields.
- Visibility and ordering keys such as `list`, `show`, `create`, `edit`, and
  `order` belong here, not in hidden runtime logic.
- Relationship names must match exposed SAFRS relationship names exactly.
- Internal rule-support columns can stay in `admin.yaml` as hidden read-only
  fields so the frontend contract remains explicit.
