from: frontend
to: architect
topic: ux package ready for review
purpose: signal that phase 3 artifacts are complete for the airport app

required reads:
- ux/navigation.md
- ux/screen-inventory.md
- ux/field-visibility-matrix.md
- ux/custom-view-specs.md
- ux/state-handling.md

requested outputs:
- architect review and implementation handoff if no contract drift remains

dependencies:
- UX package is marked `ready-for-handoff`

gate status: pass

implementation evidence:
- landing page behavior, field visibility, and state handling are explicit

blocking issues:
- none

notes:
- `FlightList` is the primary operational admin screen
