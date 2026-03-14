# Frontend Error And Loading Behavior

This file defines the required frontend handling for failures and empty states.

## admin.yaml load failure

If `/ui/admin/admin.yaml` fails to load or parse:

- show a full-page error panel
- include the failing URL
- show the underlying error message
- do not silently fall back to an empty app

## Validation errors

Expected backend shape:

- JSON:API error payload with `errors[]`
- starter v1 only guarantees a readable top-level error such as `title` and
  `detail`

Frontend behavior:

- always show a visible form-level or toast error using the backend message
- field-level mapping is optional and only in scope if the project explicitly
  defines a JSON:API pointer contract plus frontend adapter support

## Non-validation API errors

- show a toast or visible error message
- do not hide the failure behind a spinner
- leave enough context for the user to retry

## Upload errors

If the app supports uploaded files:

- failed pending-metadata creation MUST produce a visible error
- failed multipart upload MUST produce a visible error
- the frontend MUST NOT silently continue the final record save after an upload
  failure

## Custom-view errors

For `Landing.tsx` or any D3-driven summary page:

- show a visible error state in the page body
- avoid blank SVGs with no explanation

## Empty states

Lists, custom views, and charts must all define empty states explicitly.
