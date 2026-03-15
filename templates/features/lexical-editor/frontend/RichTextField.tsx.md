# `RichTextField.tsx`

Use this only when the run explicitly approves rich-text storage for a specific
resource and field.

Rules:

- keep all Lexical packages on the same version line
- define both edit and read-only rendering behavior
- do not use this as a silent upgrade for generic `text` fields
