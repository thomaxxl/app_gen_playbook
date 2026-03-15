# Frontend Spec

This directory is the detailed frontend contract for the playbook-generated app
style.

This directory is part of the playbook and defines the implementation
contract. Generated application source files must be written under `app/`, not
here.

Normative language in this directory MUST be interpreted using RFC 2119-style
semantics:

- `MUST` / `MUST NOT`: absolute implementation requirements
- `SHOULD` / `SHOULD NOT`: strong defaults that MAY be changed only with an
  explicit documented reason
- `MAY`: permitted optional behavior

The agent MUST NOT load every file by default. It MUST load only the parts
needed for the current task.

The agent MUST load these files first:

- [dependencies.md](dependencies.md)
- [scaffold.md](scaffold.md)
- [runtime-contract.md](runtime-contract.md)
- [routing-and-paths.md](routing-and-paths.md)
- [home-and-entry.md](home-and-entry.md)
- [relationship-ui.md](relationship-ui.md)
- [ui-principles.md](ui-principles.md)
- [accessibility.md](accessibility.md)

The agent MUST also consult:

- `../../runs/current/artifacts/architecture/capability-profile.md`
- `../../runs/current/artifacts/architecture/load-plan.md`

The agent MAY load these files on demand:

- [advanced-optional-packages.md](advanced-optional-packages.md)
  when evaluating optional frontend package families, package pinning policy,
  or advanced capability combinations
- [theme-and-layout.md](theme-and-layout.md)
  when changing the starter page shell, theme, spacing, card density, or other
  non-default layout behavior
- [admin-yaml-contract.md](admin-yaml-contract.md)
  when generating forms, lists, reference handling, or menu metadata
- [relationship-sparse-example.md](relationship-sparse-example.md)
  when the app has incomplete normalized relationship metadata or lacks real
  database foreign-key constraints
- [record-shape.md](record-shape.md)
  when implementing data-provider mapping or custom views
- [custom-views.md](custom-views.md)
  when adding `Landing.tsx`, dashboards, D3 figures, or extra routes
- [errors.md](errors.md)
  when handling validation, load failures, and user-visible error states
- [build-and-deploy.md](build-and-deploy.md)
  when configuring Vite build, nginx, or subpath deployment
- [validation.md](validation.md)
  when proving the generated frontend is deployable and stable
- [../../features/uploads/README.md](../../features/uploads/README.md)
  only when uploads are enabled for the run and frontend work is in scope
- [../../features/ux-measurement/README.md](../../features/ux-measurement/README.md)
  only when UX measurement is enabled for the run and frontend work is in scope
- [../../features/font-awesome-icons/README.md](../../features/font-awesome-icons/README.md)
  only when `font-awesome-icons` is enabled for the run
- [../../features/motion-animations/README.md](../../features/motion-animations/README.md)
  only when `motion-animations` is enabled for the run
- [../../features/react-virtuoso/README.md](../../features/react-virtuoso/README.md)
  only when `react-virtuoso` is enabled for the run
- [../../features/dnd-kit/README.md](../../features/dnd-kit/README.md)
  only when `dnd-kit` is enabled for the run
- [../../features/react-flow/README.md](../../features/react-flow/README.md)
  only when `react-flow` is enabled for the run
- [../../features/lexical-editor/README.md](../../features/lexical-editor/README.md)
  only when `lexical-editor` is enabled for the run
- [../../features/embla-carousel/README.md](../../features/embla-carousel/README.md)
  only when `embla-carousel` is enabled for the run
- [../../features/d3-custom-views/README.md](../../features/d3-custom-views/README.md)
  only when `d3-custom-views` is enabled for the run

Optional feature packs live under `../../features/` and MUST be loaded only
when enabled by the run capability profile. Disabled or undecided feature
packs MUST NOT be used as design input.

Disabled or irrelevant UX/UI packs MUST NOT be:

- loaded
- summarized
- used as fallback design ideas
- copied into `app/`
- treated as default UX guidance

The spec in this directory is the contract. The agent MUST NOT treat any
repo-local app as the source of truth unless the required files are also
shipped under `../../templates/`.
