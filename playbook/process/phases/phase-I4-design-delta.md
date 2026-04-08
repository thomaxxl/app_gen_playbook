# Phase I4 - Design Delta

Leads: Frontend and/or Backend

## Goal

Update only the owned design artifacts needed for the approved change.

If the change packet includes a conceptual-domain-model delta, the affected
design roles MUST use it as an input instead of inferring changed business
meaning from implementation artifacts alone.

## Outputs

- updated UX delta artifacts when the change affects UX behavior
- updated visual-direction and draft-flow-review deltas when the change affects
  visual language, navigation placement, CTA hierarchy, or form flow
- when the input prompt or change packet includes binding external UI references,
  update `runs/current/changes/<change_id>/candidate/artifacts/ux/reference-alignment.md`
  so it records the priority order `input prompt > business model/contracts >
  external reference > agent interpretation` and the exact shell/palette/
  typography/layout cues that must be mimicked
- updated backend-design delta artifacts when the change affects models, API,
  queries, bootstrap, or rules, including concept-to-model remapping when
  business concepts, states, relationships, or business events changed
- Architect review handoffs
