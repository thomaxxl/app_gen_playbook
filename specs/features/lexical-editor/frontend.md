# Lexical Editor Frontend Guidance

This feature is stricter than the other optional frontend packages because it
also changes storage and content semantics.

When enabled, the run MUST define explicitly:

- minimal supported editor profile
- persisted content format
- whether rich text is safe only for specific resources or fields
- toolbar and plugin scope
- read-only renderer expectations
- export or migration rules when HTML or Markdown is involved

Lexical MUST NOT be smuggled into ordinary `text` fields as a silent widget
upgrade.
