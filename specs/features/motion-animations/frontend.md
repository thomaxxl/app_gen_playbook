# Motion Animations Frontend Guidance

Feature-owned code SHOULD remain page- or component-local.

Approved uses:

- section reveal wrappers
- list or card transitions
- explicit gesture surfaces on custom pages

Forbidden by default:

- making generic CRUD form controls depend on Motion
- adding app-wide animation helpers to always-loaded core runtime files
