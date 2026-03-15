owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/custom-pages.md
  - ../product/workflows.md
  - ../architecture/resource-naming.md
  - ../architecture/resource-classification.md
unresolved:
  - none
last_updated_by: frontend

# Custom View Specs

## Required custom-view table

| View ID | Route | View class | Required or optional | Starter compatible | Standard page shell required | Header or hero structure | Summary sections | CTA hierarchy | Proof or reassurance model | Data joins needed | Main interactions | CTA and recovery behavior | Chart text fallback | Mobile fallback | Acceptance hooks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `HOME-001` | `/Home` | `Home` | required | no | yes | hero with primary and secondary CTA | summary-card strip plus quick actions | primary CTA to `MemberProfile`, secondary CTA to `MatchPool` and `ProfileStatus` | live counts prove backend wiring | simple count fetches only | navigate to generated routes | retry guidance on fatal bootstrap error; partial-card fallback on count failures | not applicable | stack hero, cards, and quick actions | `entry-primary-cta`, `entry-proof-strip` | no separate no-layout page |

## Required sections

- app uses only `Home`; no no-layout route
- `Landing.tsx` is omitted
- `CustomDashboard.tsx` is not required
- `Home` uses the shared page shell plus domain-specific hero copy
- summary cards expose:
  - total pools
  - total profiles
  - discoverable profiles
- the view uses summary cards rather than charts
- the view remains inside the standard React-admin shell
