# D3 Custom Views Frontend Contract

When `d3-custom-views` is enabled:

- the generated app MUST install `d3@7.9.0`
- `@types/d3@7.4.3` MAY be installed only when the chosen import or build path
  actually needs it
- D3 MUST stay inside focused visualization components
- page-level resource/runtime logic and D3 drawing logic MUST remain separate
- D3 MUST NOT be used for standard CRUD layout, ordinary cards, or general UI
  chrome

Recommended split:

- page component:
  fetches data, resolves relationships, applies filtering, and prepares a
  simple visualization input model
- visualization component:
  owns the SVG, scales, layout, and interaction details

If a D3 view is decision-critical, the page MUST also provide a concise text
summary or fallback description.
