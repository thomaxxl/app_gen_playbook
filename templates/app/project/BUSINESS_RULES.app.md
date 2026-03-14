# `app/BUSINESS_RULES.md`

See also:

- [../../../specs/product/business-rules.md](../../../specs/product/business-rules.md)
- [../../../runs/current/artifacts/product/business-rules.md](../../../runs/current/artifacts/product/business-rules.md)

This file is the generated-app copy of the current run's business-rules
catalog.

The authoritative human-readable source during generation remains:

- `runs/current/artifacts/product/business-rules.md`

The generated app MUST also contain a synchronized copy at:

- `app/BUSINESS_RULES.md`

## Required content rule

`app/BUSINESS_RULES.md` MUST be a near-verbatim copy of the approved
run-owned business-rules catalog for the app snapshot.

The generated-app copy MAY add a short header note such as:

```md
# Business Rules

This file is the generated-app snapshot of the approved business-rules
catalog used for this build.
```

After that short note, the file SHOULD preserve the rule index, stable rule
IDs, mirror modes, examples, and decision tables from the run-owned source.

## Sync rule

If `runs/current/artifacts/product/business-rules.md` changes during the run,
`app/BUSINESS_RULES.md` MUST be refreshed before delivery.

`app/BUSINESS_RULES.md` is a generated-app snapshot, not a second source of
truth.
