# Business Rules

This file is the generated-app snapshot of the approved CMDB rules used for
this build.

## Rule Index

- `CMDB-001`: `Service.ci_count` is the derived count of related
  `ConfigurationItem` rows.
- `CMDB-002`: `Service.operational_ci_count` is the derived sum of
  `ConfigurationItem.operational_value`.
- `CMDB-003`: `Service.total_risk_score` is the derived sum of
  `ConfigurationItem.risk_score`.
- `CMDB-004`: `ConfigurationItem.status_code`,
  `ConfigurationItem.is_operational`, and
  `ConfigurationItem.operational_value` are copied from the referenced
  `OperationalStatus`.
- `CMDB-005`: Configuration items in the `production` environment require
  `last_verified_at`.
- `CMDB-006`: `ConfigurationItem.risk_score` must stay between `0` and `100`.
- `CMDB-007`: `ConfigurationItem.service_id` and
  `ConfigurationItem.status_id` are required on create and update.

## Decision Notes

- Service rollups are rule-managed and must remain read-only in the admin UI.
- Operational posture is controlled through the `OperationalStatus` reference
  table instead of per-item manual toggles.
- Production verification is enforced in the backend so API and UI writes
  follow the same constraint.
