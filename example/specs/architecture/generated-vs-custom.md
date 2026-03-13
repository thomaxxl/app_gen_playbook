owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Generated Vs Custom Boundary

- generated or thin project files:
  - `frontend/src/generated/resourcePages.ts`
  - `frontend/src/generated/resources/Gate.tsx`
  - `frontend/src/generated/resources/Flight.tsx`
  - `frontend/src/generated/resources/FlightStatus.tsx`
  - `frontend/src/config.ts`
  - `frontend/src/App.tsx`
  - `frontend/src/Landing.tsx`
  - `backend/src/airport_ops/models.py`
  - `backend/src/airport_ops/bootstrap.py`
  - `backend/src/airport_ops/fastapi_app.py`
  - `backend/run.py`
  - `run.sh`
- copied shared runtime files:
  - `frontend/src/shared-runtime/**`
  - `frontend/src/shims/fs-promises.ts`
- intentionally custom project files:
  - airport-specific landing layout and summary cards
  - airport sample data
  - custom validation copy in docs and tests
  - project README and deployment notes

Edit policy:

- app-local generated files may be edited directly once the project exists
- copied shared runtime files should be treated as a shared contract and updated
  carefully
- if the runtime contract changes, update the runtime docs and templates first,
  then downstream projects
