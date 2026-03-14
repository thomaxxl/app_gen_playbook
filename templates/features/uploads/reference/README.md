# Uploads Feature Templates: Reference

Use this entrypoint only when uploads are enabled.

Load these concrete snippets:

- `../../../app/reference/admin.yaml.md`

When uploads are enabled, `admin.yaml` MUST declare the upload-backed fields
using the `file` or `image` feature-field contract rather than inventing
project-local keys.
