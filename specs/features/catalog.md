# Capability Catalog

This is the canonical catalog for optional capability packs.

| Capability | Maturity | Owner roles | Allowed in generated apps | Segmentation model | Notes |
| --- | --- | --- | --- | --- | --- |
| uploads | supported | architect, backend, frontend, devops | yes | feature-gated-with-no-op-extension-points | Full pack and validation exist |
| font-awesome-icons | supported | architect, frontend | yes | feature-gated-wrapper-swap | App-facing icon system stays optional and UX-owned |
| motion-animations | experimental | architect, frontend | yes, only when explicitly enabled | fully-isolated | Motion-based transitions and gesture-driven animation |
| react-virtuoso | experimental | architect, frontend | yes, only when explicitly enabled | fully-isolated | Large-list, table, or grid virtualization |
| dnd-kit | experimental | architect, frontend | yes, only when explicitly enabled | fully-isolated | Drag/drop and reorderable interfaces |
| react-flow | experimental | architect, frontend | yes, only when explicitly enabled | fully-isolated | Node-based editors and diagram canvases |
| lexical-editor | experimental | architect, frontend, backend | yes, only when explicitly enabled | fully-isolated | Rich-text editing requires explicit storage and field policy |
| embla-carousel | experimental | architect, frontend | yes, only when explicitly enabled | fully-isolated | Carousel support for exceptional content-driven surfaces |
| ux-measurement | experimental | architect, frontend, product-manager | yes, only when explicitly enabled | fully-isolated | No default starter instrumentation |
| d3-custom-views | supported | architect, frontend | yes, only when explicitly enabled | feature-gated-focused-components | D3 is the standard bespoke chart/SVG lane when a run requires it |
| reporting | placeholder | architect, backend, frontend, devops | no by default | placeholder-only | Pack exists as a future planning slot |
| background-jobs | placeholder | architect, backend, devops | no by default | placeholder-only | Pack exists as a future planning slot |

Catalog rules:

- capability profiles MUST use only cataloged names
- optional frontend libraries MUST be introduced only through capability packs,
  not by widening the starter dependency baseline silently
- experimental packs MUST NOT be promoted to `supported` until the repo ships
  feature-owned docs, templates, validation guidance, and at least one
  concrete test or browser-smoke path for that capability
- placeholder packs MUST remain `disabled` or `undecided` unless the current
  run expands them deliberately
- if a feature pack matures, update this file and the pack README together
