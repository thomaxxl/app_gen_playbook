# React Flow Frontend Guidance

Feature-owned code MUST define:

- controlled versus uncontrolled state ownership
- starter node and edge type policy
- canvas layout and resize behavior
- zoom and pan expectations
- persisted node and edge data shape

React Flow MUST remain out of core dashboard or `Home` templates unless the
run explicitly enables it.
