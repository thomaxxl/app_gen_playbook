# `app/BUSINESS_RULES.md`

See also:

- [../../../specs/product/business-rules.md](../../../specs/product/business-rules.md)
- [../../../runs/current/artifacts/product/business-rules.md](../../../runs/current/artifacts/product/business-rules.md)

This file is an optional generated-app export of the current run's
business-rules catalog.

The authoritative human-readable source during generation remains:

- `runs/current/artifacts/product/business-rules.md`

If the current product brief or delivery flow explicitly requests an app-local
business-rules export, the generated app MAY contain a synchronized copy at:

- `app/BUSINESS_RULES.md`

## Export content rule

When this export is requested, `app/BUSINESS_RULES.md` SHOULD be a near-verbatim
copy of the approved
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

If this export is enabled and
`runs/current/artifacts/product/business-rules.md` changes during the run,
`app/BUSINESS_RULES.md` SHOULD be refreshed before delivery.

`app/BUSINESS_RULES.md` is a generated-app snapshot, not a second source of
truth.
