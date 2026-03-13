from: architect
to: backend
topic: airport-operations backend-design package
purpose: start phase 4 using the approved cross-layer contract

required reads:
- architecture/overview.md
- architecture/domain-adaptation.md
- architecture/integration-boundary.md
- architecture/resource-naming.md
- architecture/generated-vs-custom.md
- architecture/test-obligations.md
- product/brief.md
- product/business-rules.md
- product/sample-data.md

requested outputs:
- backend-design/model-design.md
- backend-design/relationship-map.md
- backend-design/rule-mapping.md
- backend-design/bootstrap-strategy.md
- backend-design/test-plan.md

dependencies:
- architecture package is marked `ready-for-handoff`

gate status: pass

implementation evidence:
- airport resource naming and route model are fixed

blocking issues:
- none

notes:
- verify `FlightStatus` route naming carefully during implementation
