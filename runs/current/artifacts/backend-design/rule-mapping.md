owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/business-rules.md
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Rule Mapping

| Rule ID | Backend fields involved | Backend enforcement location | LogicBank pattern | API behavior | Backend tests | Frontend mirror mode | Frontend mirror location | Frontend tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-001 | `Gate.scheduled_flights`, `Flight` rows | `rules.py` | count | derived update | `test_rules.py`, `test_bootstrap.py` | none | none | none | gate count |
| BR-002 | `Gate.active_flights`, `Flight.is_active` | `rules.py` | sum | derived update | `test_rules.py` | none | none | none | boolean sum via integer flags |
| BR-003 | `Gate.total_delay_minutes`, `Flight.delay_minutes` | `rules.py` | sum | derived update | `test_rules.py` | none | none | none | delay aggregation |
| BR-004 | `Flight.flight_status_code`, `Flight.is_active`, `Flight.requires_attention` | `rules.py` | copy | derived update | `test_rules.py` | none | none | none | parent status copy |
| BR-005 | `Flight.gate_id`, `Flight.status_id` | `models.py`, `fastapi_app.py` | custom validator | save rejected | `test_bootstrap.py`, `test_api_contract.py` | form | `generated/resources/Flight.tsx` | `SchemaDrivenAdminApp.smoke.test.tsx` | both refs required |
| BR-006 | `Flight.delay_minutes` | `models.py` | custom validator | save rejected | `test_bootstrap.py`, `test_rules.py` | input | `generated/resources/Flight.tsx` | `SchemaDrivenAdminApp.smoke.test.tsx` | non-negative |
| BR-007 | `Flight.requires_attention`, `Flight.delay_reason` | `rules.py` | constraint | save rejected | `test_rules.py`, `test_api_contract.py` | form | `generated/resources/Flight.tsx` | `SchemaDrivenAdminApp.smoke.test.tsx` | attention reason |
| BR-008 | `Flight.flight_status_code`, `Flight.actual_departure_at` | `rules.py` | constraint | save rejected | `test_rules.py`, `test_api_contract.py` | form | `generated/resources/Flight.tsx` | `SchemaDrivenAdminApp.smoke.test.tsx` | departure timestamp |

## Notes

- BR-001 through BR-004 are declarative LogicBank rules.
- BR-005 and BR-006 use SQLAlchemy validation plus flush-time checks.
- BR-007 and BR-008 use LogicBank constraint rules.
