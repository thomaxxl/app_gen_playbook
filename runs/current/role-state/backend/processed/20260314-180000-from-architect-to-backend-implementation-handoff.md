from: architect
to: backend
topic: implementation handoff
purpose: start backend implementation against approved contracts
required reads:
  - runs/current/artifacts/architecture/*
  - runs/current/artifacts/product/*
  - runs/current/artifacts/backend-design/*
requested outputs:
  - implemented backend
dependencies:
  - product, architecture, ux, backend-design packages
gate status: pass
implementation evidence:
  - no unresolved contract drift at handoff time
blocking issues:
  - none
notes:
  - remove upload routes from the preserved example scaffold
