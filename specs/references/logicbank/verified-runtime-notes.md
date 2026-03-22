# Verified LogicBank Runtime Notes

This note records the current repo-maintained LogicBank compatibility snapshot
for the backend runtime expected by the playbook.

Refresh it with:

```bash
PYTHONPATH=tools python3 tools/verify_logicbank_runtime_contract.py --repo-root . --json
```

The current verified baseline is:

- `LogicBank.activate(session, activator, constraint_event=None, aggregate_defaults=False, all_defaults=False)`
- `LogicRow.log(self, msg: str) -> str`
- `LogicRow.new_logic_row(self, new_row_class: sqlalchemy.orm.decl_api.DeclarativeMeta) -> LogicRow`
- row-event callbacks execute through keyword calling style:
  `calling(row=..., old_row=..., logic_row=...)`
- `logic_row.new_logic_row(ModelClass)` is the verified nested-row creation
  helper
- `early_row_event` is the preferred response-bearing request-pattern lane
- `after_flush_row_event` is the preferred fire-and-forget side-effect lane

This note is a maintained baseline, not the source of truth. If it drifts from
the installed package, refresh the verification script output and update the
playbook contract accordingly.
