# Web / GenAI Suggestions

Portable summary of the playbook stance on natural-language rule drafting:

- suggestions are draft input only, not source of truth
- generated suggestions may imply new fields, relationships, or test-data
  changes that must be reviewed explicitly
- no WebGenAI or auto-discovery flow is part of the default backend read path
- if used at all, the translated result must still be reconciled into
  `model-design.md`, `rule-mapping.md`, and `test-plan.md`
