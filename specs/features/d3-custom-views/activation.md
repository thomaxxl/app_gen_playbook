# D3 Custom Views Activation

Enable `d3-custom-views` only when run-owned UX artifacts explicitly require:

- charts
- trees
- network or relationship diagrams
- SVG dashboards
- other bespoke visualizations that exceed the shared admin shell

Do not enable this pack just because a chart "might be nice".

Activation requirements:

- `runs/current/artifacts/ux/custom-view-specs.md` MUST name the page that uses
  D3
- that UX artifact MUST state what the visualization communicates
- the Architect MUST mark the capability as `enabled` in
  `runs/current/artifacts/architecture/capability-profile.md`
- the Architect MUST list this pack in the Frontend role section of
  `runs/current/artifacts/architecture/load-plan.md`

When disabled or undecided:

- do not read this pack as design input
- do not install `d3`
- do not copy D3-specific templates into `app/`
