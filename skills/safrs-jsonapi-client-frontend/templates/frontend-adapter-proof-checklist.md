# Frontend Adapter Proof Checklist

Use this checklist in frontend validation and Architect review.

## Package source
- [ ] `runtime-bom.md` records the approved `safrs-jsonapi-client` repo, checkout policy, and local materialization path
- [ ] generated `package.json` uses the approved local `file:../tmp/safrs-jsonapi-client` source
- [ ] install source comes from the approved local checkout, not a floating git dependency or raw source archive

## Canonical adapter
- [ ] runtime creates the base provider from `safrs-jsonapi-client`
- [ ] local wrappers are extensions around the package provider, not replacements
- [ ] no delivered component code performs direct backend `fetch(...)`

## Schema / admin.yaml
- [ ] playbook `admin.yaml` is either passed directly to the package normalizer or adapted into the package input shape
- [ ] `endpoint`, `user_key`, search metadata, and `tab_groups` survive the adapter path
- [ ] relationship ordering / labels still match author-authored `tab_groups`

## Record shape
- [ ] list records preserve `id`
- [ ] list records preserve `ja_type`
- [ ] list records preserve `attributes`
- [ ] list records preserve `relationships`
- [ ] flattened attributes are still available
- [ ] embedded related objects survive when the package would provide them

## Search wrapper
- [ ] `q` search still preserves package-compatible record shape
- [ ] `include=...` survives the search path
- [ ] searched list results still support relationship display
- [ ] search totals remain correct

## Relationship UI
- [ ] related-record UI uses embedded include data first
- [ ] then uses canonical parent relationship route
- [ ] then uses `getOne(...)` fallback by id
- [ ] no custom helper endpoints were introduced for ordinary DB-backed relationships

## RPC / services
- [ ] SAFRS RPC-style methods use `execute()`
- [ ] raw JSON service calls use `execute(..., { mode: "raw" })`
- [ ] error handling remains consistent with the package provider

## Tests
- [ ] unit or integration test proves search-wrapper compatibility
- [ ] unit or integration test proves relationship tab/dialog behavior
- [ ] unit or integration test proves included related data survives normalization
- [ ] unit or integration test proves a representative `execute()` call
