# Runs

This directory distinguishes:

- `template/`
  The tracked neutral starter workspace
- local `current/`
  The active run workspace created from `template/`

Rules:

- `template/` MUST stay neutral and reusable
- local `current/` MUST be created from `template/` at run start
- generated apps and run-owned artifacts MUST NOT treat `template/` as a real
  prior project
- `template/` SHOULD contain the neutral starter gating files needed to create
  `current/` without guesswork
