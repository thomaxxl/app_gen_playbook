# Process Core Summary

Load this when a role needs the minimum shared process model.

The run model is:

- tracked neutral starter in `runs/template/`
- local active run in `runs/current/`
- local generated app in `app/`

The minimal process rules are:

- create local `runs/current/` from `runs/template/` for a new run
- use `runs/current/input.md` as the canonical brief
- use capability profile and load plan before loading optional packs
- use task bundles to decide the smallest valid file set for the current task
- record decisions in owned run artifacts, not only in inbox items
- final delivery requires real verification evidence, including Playwright
  when applicable

This file does not define detailed phase gates or role ownership.

Load next when needed:

- the relevant phase summary
- the relevant phase file
- the relevant task bundle
- `playbook/process/loading-protocol.md`
