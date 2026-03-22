# LogicBank Repo-Local References

This directory contains portable repo-local summaries of the LogicBank
reference material the playbook relies on for advanced guidance.

These notes are not the source of truth for package signatures.

Use the files in this directory as follows:

- background summaries:
  `logic-overview.md`, `database-changes.md`, `request-pattern.md`,
  `allocation.md`, `webgenai-suggestions.md`
- verified compatibility note:
  `verified-runtime-notes.md`
- reproducible verification entrypoint:
  `../../tools/verify_logicbank_runtime_contract.py`
  which now includes a real in-memory LogicBank smoke transaction rather than
  source inspection alone

For verified runtime behavior, use:

- `../../contracts/rules/logicbank-reference.md`
- the installed `logicbank` package in the backend runtime

Use these files as scoped background:

- `logic-overview.md`
- `database-changes.md`
- `request-pattern.md`
- `allocation.md`
- `webgenai-suggestions.md`
