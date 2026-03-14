owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
unresolved:
  - final wire type values must still be runtime-verified
last_updated_by: architect

# Resource Naming

| Domain Resource | Python Model Class | SQL Table | admin.yaml Key | Expected SAFRS Wire Type | Collection Path | Relationship Names |
| --- | --- | --- | --- | --- | --- | --- |
| Gate | `Gate` | `gates` | `Gate` | `Gate` (verify at runtime) | `/api/gates` | `flights` |
| Flight | `Flight` | `flights` | `Flight` | `Flight` (verify at runtime) | `/api/flights` | `gate`, `status` |
| FlightStatus | `FlightStatus` | `flight_statuses` | `FlightStatus` | `FlightStatus` (verify at runtime) | `/api/flight_statuses` | `flights` |

## Naming rules

- ORM column names remain `snake_case`.
- Relationship names are literal contract terms and must match `admin.yaml`.
- Backend tests must verify the actual wire types rather than trusting these
  expected values blindly.
