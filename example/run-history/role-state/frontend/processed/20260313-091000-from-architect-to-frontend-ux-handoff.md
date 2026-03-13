from: architect
to: frontend
topic: airport-operations ux package
purpose: start phase 3 using the approved cross-layer contract

required reads:
- architecture/overview.md
- architecture/domain-adaptation.md
- architecture/integration-boundary.md
- architecture/resource-naming.md
- architecture/route-and-entry-model.md
- architecture/generated-vs-custom.md
- architecture/test-obligations.md
- product/brief.md
- product/workflows.md
- product/custom-pages.md

requested outputs:
- ux/navigation.md
- ux/screen-inventory.md
- ux/field-visibility-matrix.md
- ux/custom-view-specs.md
- ux/state-handling.md

dependencies:
- architecture package is marked `ready-for-handoff`

gate status: pass

implementation evidence:
- route, naming, and generated/custom boundaries are fixed for the airport app

blocking issues:
- none

notes:
- keep the landing page operational rather than decorative
