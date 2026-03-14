from: backend
to: architect
topic: integration review
purpose: submit generated backend for cross-layer review
required reads:
  - app/backend/src/airport_ops/
  - runs/current/evidence/backend-tests.md
requested outputs:
  - architect integration review
dependencies:
  - backend implementation
gate status: pass with assumptions
implementation evidence:
  - backend code generated locally under app/
blocking issues:
  - dependency-backed pytest execution not run
notes:
  - airport domain conversion completed across models, rules, bootstrap, and API tests
