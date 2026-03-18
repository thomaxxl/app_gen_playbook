# UI Preview Manifest

starter_status: pending-review-evidence

Replace this starter note during Phase 6 or Phase 7.

Required fields:

- `capture_status: captured` when reviewable screenshots were produced
- `capture_status: not-required` when the run did not materially change visible
  UI
- `capture_status: environment-blocked` when screenshots would have been
  appropriate but browser execution was unavailable

When `capture_status: captured`, list:

- the command used, typically `npm run capture:ui-previews`
- the reviewed routes or surfaces
- the generated screenshot files that Product can review
