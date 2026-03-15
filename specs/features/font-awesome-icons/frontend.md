# Font Awesome Frontend Contract

When `font-awesome-icons` is enabled, the generated frontend MUST install:

- `@fortawesome/react-fontawesome@3.2.0`
- `@fortawesome/fontawesome-svg-core@7.2.0`
- `@fortawesome/free-solid-svg-icons@7.2.0`

Optional packs MAY be added only when the run-owned UX iconography artifact
approves them:

- `@fortawesome/free-regular-svg-icons@7.2.0`
- `@fortawesome/free-brands-svg-icons@7.2.0`

Implementation rules:

- app-facing visible icons SHOULD be rendered through a shared `AppIcon`
  wrapper
- the same repeated UI surface MUST NOT mix icon families by default
- sidebar, CTA, summary-card, quick-action, and entry-page icons MUST follow
  `runs/current/artifacts/ux/iconography.md`
- direct MUI icon imports SHOULD be treated as a transitional implementation
  detail only when `iconography.md` explicitly allows them
