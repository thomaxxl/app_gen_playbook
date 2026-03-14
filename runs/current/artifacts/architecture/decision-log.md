owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Decision Log

1. The run is classified as `rename-only`, not `starter` and not `non-starter`.
2. The product scope is limited to departure gate operations.
3. All optional capability packs are disabled.
4. `Home` and `Landing` are both included; `Home` remains the primary in-admin
   entry route.
5. The generated app keeps the preserved example runtime stack with noted
   dependency-source deviations rather than repinning packages during this run.
