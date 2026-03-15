# Capability Catalog

This is the canonical catalog for optional capability packs.

| Capability | Maturity | Owner roles | Allowed in generated apps | Segmentation model | Notes |
| --- | --- | --- | --- | --- | --- |
| uploads | supported | architect, backend, frontend, devops | yes | feature-gated-with-no-op-extension-points | Full pack and validation exist |
| font-awesome-icons | supported | architect, frontend | yes | feature-gated-wrapper-swap | App-facing icon system stays optional and UX-owned |
| ux-measurement | experimental | architect, frontend, product-manager | yes, only when explicitly enabled | fully-isolated | No default starter instrumentation |
| d3-custom-views | supported | architect, frontend | yes, only when explicitly enabled | feature-gated-focused-components | D3 is the standard bespoke chart/SVG lane when a run requires it |
| reporting | placeholder | architect, backend, frontend, devops | no by default | placeholder-only | Pack exists as a future planning slot |
| background-jobs | placeholder | architect, backend, devops | no by default | placeholder-only | Pack exists as a future planning slot |

Catalog rules:

- capability profiles MUST use only cataloged names
- placeholder packs MUST remain `disabled` or `undecided` unless the current
  run expands them deliberately
- if a feature pack matures, update this file and the pack README together
