# Playbook Remarks

## Observed During This Run

- The user asked for a `"cimage"` app, which reads like a typo of `"image"`.
  The playbook does not say whether likely typos in app names should be
  normalized or preserved. I preserved `Cimage` as the product name.
- App-only mode is now documented and workable, but an empty `app/` still has
  no canonical stub `README.md` or `REMARKS.md`. A tiny starter template would
  reduce ambiguity at generation time.
- The previous preserved example scaffold was airport-specific, which made
  non-airport runs harder to adapt. This has since been corrected by replacing
  the preserved example with the Cimage app.
- Backend dependency guidance is still inconsistent with reality on this host:
  `logicbank==1.30.1` and `SQLAlchemy==2.0.48` do not install cleanly together
  from a single `requirements.txt`, so verification still needs a split install
  where LogicBank is added with `--no-deps`.
- LogicBank behavior is subtler than the current playbook suggests. Copy rules
  worked reliably on child create/update/reassignment, but changing fields on a
  referenced parent status did not obviously back-propagate to already-linked
  child rows in this setup. The playbook should clarify whether that propagation
  is expected, required, or out of scope.
- Frontend dependency delivery is still brittle. Installing
  `safrs-jsonapi-client` from Git transport is unreliable here, while the
  GitHub tarball installs but requires Vite/TypeScript aliasing to the package's
  `src/index.ts` because the distributed `dist/` entry is not available in the
  installed artifact.
- Frontend test naming is easier to get wrong than it looks. A file named
  `vite.config.test.ts` was excluded by Vitest's default config-file ignore
  pattern, and the Vite config test also needed an explicit Node test
  environment instead of the suite-wide `jsdom` default. The playbook should
  call out both constraints for config-level tests.
- Environment guidance still needs to be more explicit for mounted filesystems.
  `pip --target` and a temp frontend copy were the reliable verification path;
  the playbook should make that fallback a first-class documented option instead
  of an implementation detail discovered during the run.
