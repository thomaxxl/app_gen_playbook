# `frontend/src/CustomDashboard.tsx` for a non-starter app

Use this template when the custom default page should be generic rather than a
starter-domain `Landing.tsx`.

The implementation MUST derive its content from:

- `../../../runs/current/artifacts/product/custom-pages.md`
- `../../../runs/current/artifacts/ux/custom-view-specs.md`
- `../../../runs/current/artifacts/ux/state-handling.md`

Rules:

- it MUST live inside the React-admin data-provider context
- it MUST NOT depend on starter-domain resource names
- it SHOULD become the default non-starter custom page
