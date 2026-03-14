from: architect
to: frontend
topic: implementation handoff
purpose: start frontend implementation against approved contracts
required reads:
  - runs/current/artifacts/architecture/*
  - runs/current/artifacts/product/*
  - runs/current/artifacts/ux/*
requested outputs:
  - implemented frontend
dependencies:
  - product, architecture, ux, backend-design packages
gate status: pass
implementation evidence:
  - no unresolved contract drift at handoff time
blocking issues:
  - none
notes:
  - preserve `/admin-app/` route model and `Home` resource entry
