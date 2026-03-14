from: backend
to: architect
topic: backend package handoff
purpose: submit backend-design artifacts for implementation review
required reads:
  - runs/current/artifacts/backend-design/model-design.md
  - runs/current/artifacts/backend-design/rule-mapping.md
  - runs/current/artifacts/backend-design/test-plan.md
requested outputs:
  - implementation gate review
dependencies:
  - runs/current/artifacts/backend-design/
gate status: pass
implementation evidence:
  - backend-design artifacts marked ready-for-handoff
blocking issues:
  - none
notes:
  - active-flight rollup uses boolean-sum logic
