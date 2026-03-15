# Segmentation Model

This file defines the allowed capability-segmentation models for maintainers.

## Allowed models

1. `core-only`
   - the capability has no optional feature pack
2. `feature-gated-with-no-op-extension-points`
   - the optional feature pack owns activation
   - core runtime MAY contain dormant no-op hooks
3. `fully-isolated`
   - the optional feature pack owns the whole implementation lane
   - core runtime MUST NOT contain feature-specific hooks
4. `placeholder-only`
   - the named pack exists only as a future placeholder
   - it MUST NOT be treated as implementation-ready

## Core-hook acceptance rule

A dormant core hook is allowed only if:

- it compiles and behaves as a no-op when the feature is disabled
- it does not force extra required runtime dependencies when the feature is
  disabled
- it does not expand the required read set for unrelated runs
- the owning feature pack declares the `feature-gated-with-no-op-extension-points`
  model explicitly

## Catalog rule

Every feature pack listed under `specs/features/` MUST appear in the canonical
feature catalog with:

- owner roles
- maturity
- segmentation model
- whether it is allowed in generated apps today
