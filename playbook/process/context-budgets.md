# Context Budgets

Use this file to preserve the retrieval-first design of the playbook.

## Editorial budgets

- summary files SHOULD stay within roughly 200 to 500 words
- role entrypoint files SHOULD stay under roughly 900 words when practical
- task bundles SHOULD stay under roughly 150 lines
- contract summary files SHOULD stay under roughly 500 words
- full contracts MAY be longer, but SHOULD be split by topic
- one concept SHOULD live in one file where practical

## Loading budgets

For a normal task, a role SHOULD need only:

1. `playbook/summaries/global-core.md`
2. `playbook/summaries/process-core.md`
3. one role summary
4. one Tier 1 read-set manifest
5. one task bundle
6. the minimum required run-owned artifacts for that task
7. enabled feature packs only

## Maintenance rule

Maintainers MUST NOT expand role startup reads or task bundles casually.

If a change increases the default read set, the maintainer MUST document why
the extra load is necessary and why the information cannot stay in a later
expansion layer.
