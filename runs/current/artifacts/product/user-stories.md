owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: architect

# User Stories

| Story ID | Actor | Story statement | Priority | Related workflow IDs | Related resources | Acceptance note |
| --- | --- | --- | --- | --- | --- | --- |
| `US-001` | Profile Operations Manager | As an operations manager, I want to create and organize match pools so I can manage profile inventory by market or cohort. | must | `WF-001` | `MatchPool` | pool CRUD is available and searchable |
| `US-002` | Profile Operations Manager | As an operations manager, I want to create and edit member profiles so I can keep discoverable records accurate. | must | `WF-002` | `MemberProfile` | create and edit forms cover the full profile contract |
| `US-003` | Trust and Safety Coordinator | As a trust and safety coordinator, I want discoverable profiles to require approval timestamps so site-visible records have a review signal. | must | `WF-002` | `MemberProfile`, `ProfileStatus` | invalid saves are rejected and explained |
| `US-004` | Profile Operations Manager | As an operations manager, I want discoverability state to follow the selected status definition so profile visibility is consistent. | must | `WF-002` | `MemberProfile`, `ProfileStatus` | copied status fields are backend-managed |
| `US-005` | Profile Operations Manager | As an operations manager, I want a dashboard home page so I can understand the profile workload and jump into the main task quickly. | should | `WF-003` | `MatchPool`, `MemberProfile`, `ProfileStatus` | Home shows purpose, proof cues, and quick actions |
| `US-006` | Trust and Safety Coordinator | As a coordinator, I want to search profiles by name, city, and status-related fields so I can find records that need review. | should | `WF-002`, `WF-003` | `MemberProfile` | list search returns matching profiles without custom reporting |
