from: product_manager
to: architect
topic: airport-operations product handoff
purpose: hand off the researched product package for architecture contract work

required reads:
- product/input-interpretation.md
- product/research-notes.md
- product/brief.md
- product/user-stories.md
- product/workflows.md
- product/domain-glossary.md
- product/business-rules.md
- product/custom-pages.md
- product/acceptance-criteria.md
- product/sample-data.md
- product/assumptions-and-open-questions.md

requested outputs:
- architecture/overview.md
- architecture/domain-adaptation.md
- architecture/integration-boundary.md
- architecture/resource-naming.md
- architecture/route-and-entry-model.md
- architecture/generated-vs-custom.md
- architecture/test-obligations.md
- architecture/decision-log.md

dependencies:
- product package is marked `ready-for-handoff`

gate status: pass with assumptions

implementation evidence:
- sparse input normalized into a single-airport departure-operations scope
- custom landing page is required
- rule candidates are documented in plain language

blocking issues:
- none

notes:
- please validate the route and naming strategy carefully for `FlightStatus`
