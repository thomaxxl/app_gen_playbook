# Conceptual Domain Model

## Purpose and scope

This preserved example captures the business-facing conceptual layer for the
CMDB operations console. It defines the concepts, relationships, states, and
business events without collapsing them into SAFRS resources, ORM classes, or
database-first naming.

## Domain areas

| Area ID | Name | Purpose | Notes |
| --- | --- | --- | --- |
| `DA-001` | Service management | Business-facing ownership and health of managed services | Primary operational context for the app |
| `DA-002` | Configuration inventory | Track the configuration items that support each service | Focuses on inventory and posture, not deployment automation |
| `DA-003` | Operational status policy | Define the allowed operational posture vocabulary | Shared reference language used across services and items |

## Business concepts

| Concept ID | Name | Area ID | Kind | Definition | Business identity | Lifecycle ID | Primary actors | Workflow IDs | Rule IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C-001` | Service | `DA-001` | entity | A managed business or technical service whose operational posture is reviewed as a unit | service name plus owner context | `LC-001` | operator, service manager | `WF-001` | `BR-001`, `BR-002`, `BR-003` | Service totals are business-facing summaries, not separate concepts |
| `C-002` | Configuration Item | `DA-002` | entity | An operational asset or component that supports one service | CI tag or inventory key | `LC-002` | operator | `WF-002` | `BR-004`, `BR-005`, `BR-006` | Includes posture, verification, and local risk context |
| `C-003` | Operational Status | `DA-003` | reference-data | The approved business-facing posture vocabulary applied to configuration items | status code | none | operator, administrator | `WF-003` | `BR-007` | Defines copied posture semantics for downstream concepts |

## Concept relationships

| Relationship ID | From Concept | To Concept | Meaning | Cardinality | Rule IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `REL-001` | `C-001` | `C-002` | A service is supported by configuration items | one-to-many | `BR-001`, `BR-002`, `BR-003` | Service totals are derived from related items |
| `REL-002` | `C-002` | `C-003` | A configuration item uses one approved operational status | many-to-one | `BR-007` | Status selection drives copied posture fields |

## Lifecycle models

### LC-001 - Service operational posture

| State | Meaning | Entered by | Exit paths | Rule IDs | Workflow IDs |
| --- | --- | --- | --- | --- | --- |
| healthy | Supporting items are operational within accepted risk | roll-up recalculation | warning, degraded | `BR-001`, `BR-002`, `BR-003` | `WF-001` |
| warning | Some supporting items need attention but the service remains usable | roll-up recalculation | healthy, degraded | `BR-001`, `BR-002`, `BR-003` | `WF-001` |
| degraded | Supporting item posture or risk has crossed the accepted threshold | roll-up recalculation | warning, healthy | `BR-001`, `BR-002`, `BR-003` | `WF-001` |

### LC-002 - Configuration item posture

| State | Meaning | Entered by | Exit paths | Rule IDs | Workflow IDs |
| --- | --- | --- | --- | --- | --- |
| active | Item is operational and contributing to service totals | create or status update | maintenance, retired | `BR-004`, `BR-007` | `WF-002` |
| maintenance | Item is intentionally unavailable or under review | status update | active, retired | `BR-004`, `BR-007` | `WF-002` |
| retired | Item no longer contributes to active posture | status update | none | `BR-004`, `BR-007` | `WF-002` |

## Business events

| Event ID | Name | Trigger | Concepts affected | State change | Rule IDs | Workflow IDs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EV-001` | Configuration item status changed | Operator updates the item status selection | `C-002`, `C-003` | `active -> maintenance`, `maintenance -> active`, etc. | `BR-004`, `BR-007` | `WF-002` | Applies the approved posture vocabulary to the item |
| `EV-002` | Service totals recalculated | A supporting item changes posture, risk, or operational contribution | `C-001`, `C-002` | healthy/warning/degraded may change | `BR-001`, `BR-002`, `BR-003` | `WF-001` | Roll-up event visible to service owners and operators |

## Concept-to-resource hints

| Concept ID | Likely application shape | Notes |
| --- | --- | --- |
| `C-001` | first-class resource | Core review surface for operators and service managers |
| `C-002` | first-class resource | Primary maintenance and posture-management record |
| `C-003` | reference/status resource | Shared controlled vocabulary used by configuration items |

## Deferred or ambiguous concepts

- incident management is intentionally out of scope for this preserved example
- change-request workflows are deferred even though they may exist in adjacent service-management systems
- risk policy tuning remains a Product/Architecture concern rather than a separate first-class concept in this starter example
