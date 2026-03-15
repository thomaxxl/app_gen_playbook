# D3 Custom Views Validation

When `d3-custom-views` is enabled, the run MUST prove:

- at least one D3 visualization component renders without console errors
- the generated frontend build still passes
- the affected custom page has a documented loading, empty, and error state
- the affected custom page has a documented narrow-width fallback when the
  chart appears on `Home`, a dashboard, or another above-the-fold view
- a text label, title, or summary accompanies the visualization when it
  carries core meaning
