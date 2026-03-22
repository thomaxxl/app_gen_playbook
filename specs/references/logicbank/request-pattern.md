# Request Pattern

Portable summary of the optional Request Pattern lane:

- use request/response or audit rows when the request itself is important
  persisted data or when rule-derived response fields must be returned
- keep the transport wrapper thin; the business logic remains in LogicBank
- use `early_row_event` when the caller needs response-bearing values in the
  same transaction
- use `after_flush_row_event` for fire-and-forget side effects that need
  flushed persistence state
- when nested rows are created during rule execution, prefer
  `logic_row.new_logic_row(ModelClass)` plus `.insert(...)`
