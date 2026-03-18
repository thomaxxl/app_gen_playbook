# UI Preview Evidence

Use local `runs/current/evidence/ui-previews/` for Playwright-captured preview
screenshots when a run materially changes visible UI.

Keep a sibling `manifest.md` here so acceptance can tell whether screenshot
absence means:

- `captured`
- `not-required`
- `environment-blocked`

Typical examples:

- `home.png`
- `resource-list.png`
- `resource-show-relationships.png`
- `resource-edit-form.png`
- `custom-view.png`

Only capture this evidence when it adds value:

- entry-page, layout, or custom-view changes
- relationship dialog/tab changes
- meaningful form-layout or responsive behavior changes

Backend-only or otherwise non-visible work does not require preview
screenshots.

These screenshots support, but do not replace, the required
`runs/current/evidence/frontend-usability.md` review record.
