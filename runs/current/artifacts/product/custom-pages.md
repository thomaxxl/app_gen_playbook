owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - user-stories.md
unresolved:
  - none
last_updated_by: architect

# Custom Pages

## HOME-001 - Home dashboard

- page ID: `HOME-001`
- purpose: summarize operational state and guide the user into the main
  profile-review workflow
- intended user:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- why generated resource pages are insufficient:
  - generated CRUD does not explain the app purpose or present the primary
    next step on entry
- entry behavior:
  - route: `/admin-app/#/Home`
  - visible menu entry: yes
- required data:
  - total match pools
  - total member profiles
  - total discoverable profiles
- key actions or links:
  - primary CTA to `MemberProfile`
  - secondary CTA to `MatchPool`
  - secondary CTA to `ProfileStatus`
- success criteria:
  - users can understand the app purpose quickly
  - users can reach the main workflow without sidebar discovery
