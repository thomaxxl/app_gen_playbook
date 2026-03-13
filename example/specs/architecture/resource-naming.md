owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
unresolved:
  - actual SAFRS collection paths and wire types must still be confirmed against the running app
last_updated_by: architect

# Resource Naming Contract

| Domain resource | Python model class | SQL table | admin.yaml resource key | SAFRS wire type | SAFRS collection path | Important relationships |
| --- | --- | --- | --- | --- | --- | --- |
| Gate | `Gate` | `gates` | `Gate` | runtime-validated | `/api/gates` target pending runtime check | `flights` |
| Flight | `Flight` | `flights` | `Flight` | runtime-validated | `/api/flights` target pending runtime check | `gate`, `status` |
| Flight Status | `FlightStatus` | `flight_statuses` | `FlightStatus` | runtime-validated | `/api/flight_statuses` target pending runtime check | `flights` |

Naming rules:

- Python model classes remain PascalCase
- `admin.yaml` resource keys are explicit project decisions
- ORM scalar columns use snake_case for writable FK storage, in this app
  `gate_id` and `status_id`
- SAFRS wire `type` values and collection paths must be discovered from the
  running backend rather than inferred from SQL naming theory
- relationship endpoint names come from the ORM relationship attribute names and
  must match `admin.yaml` tab-group and relationship references

## Multi-word resource strategy

For custom domains with multi-word resources such as `FlightStatus`:

- the Python class name MUST remain PascalCase: `FlightStatus`
- the `admin.yaml` resource key MUST match the chosen resource name exactly:
  `FlightStatus`
- the SQL table name MAY use plural snake case: `flight_statuses`
- ORM relationship attributes SHOULD remain lower-case Python names such as
  `status` and `flights`
- the final SAFRS collection path MUST be treated as a runtime-validated fact,
  not as an inferred guarantee from the table name
- the architect SHOULD record a provisional expected path in this file and
  MUST mark it unresolved until runtime validation confirms the actual path

## Route validation method

Final collection-path validation for custom resources MUST happen after the
backend starts. The validation source MUST be one or both of:

- the live SAFRS/OpenAPI output at `/jsonapi.json`
- backend integration tests that compare live collection paths with
  `admin.yaml endpoint` values

The startup bootstrap validator MUST NOT hardcode final collection paths before
route exposure.
