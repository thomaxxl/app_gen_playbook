# Capability Catalog

This is the canonical catalog for optional capability packs.

| Capability | Maturity | Owner roles | Allowed in generated apps | Segmentation model | Notes |
| --- | --- | --- | --- | --- | --- |
| uploads | supported | architect, backend, frontend, devops | yes | feature-gated-with-no-op-extension-points | Full pack and validation exist |
| ux-measurement | experimental | architect, frontend, product-manager | yes, only when explicitly enabled | fully-isolated | No default starter instrumentation |
| d3-custom-views | placeholder | architect, frontend | no by default | placeholder-only | Enable only with explicit run approval |
| reporting | placeholder | architect, backend, frontend, devops | no by default | placeholder-only | Pack exists as a future planning slot |
| background-jobs | placeholder | architect, backend, devops | no by default | placeholder-only | Pack exists as a future planning slot |

Catalog rules:

- capability profiles MUST use only cataloged names
- placeholder packs MUST remain `disabled` or `undecided` unless the current
  run expands them deliberately
- if a feature pack matures, update this file and the pack README together
