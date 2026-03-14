# UX Measurement Feature Templates

This feature-template entrypoint exists so the capability-loading rules can
refer to a concrete template boundary.

The starter playbook does not ship reusable measurement code snippets by
default.

If the run enables `ux-measurement`, the implementation team MUST add
app-local instrumentation code deliberately inside `app/` and MUST keep that
work traceable to the approved measurement scope.

If the feature is disabled or undecided, this entrypoint MUST NOT be loaded or
used as fallback design input.
