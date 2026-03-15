# Font Awesome Validation

When `font-awesome-icons` is enabled, the run MUST prove:

- the generated frontend build passes with the Font Awesome dependency set
- at least one visible page such as `Home` renders a Font Awesome-backed icon
- no unresolved direct-import starter usage remains in the surfaces that were
  meant to migrate to `AppIcon`
- the iconography decision is recorded in
  `runs/current/artifacts/ux/iconography.md`
