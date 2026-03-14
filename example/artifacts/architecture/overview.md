# Architecture Overview

## Purpose

Cimage is a SAFRS/FastAPI admin app for image sharing and management.

## Chosen app framing

The preserved example is framed as an internal admin app for managing
galleries, uploaded image assets, and release states for sharing.

## Main resources

- `Gallery`
- `ImageAsset`
- `ShareStatus`

## House-style fit

This example uses the `rename-only` lane. It keeps the starter trio's
structural intent while renaming the resources to fit the domain.

## Frontend shape

- schema-driven React-Admin CRUD pages remain the default shell
- `/admin-app/#/Home` is the required in-admin entry page
- `/admin-app/#/Landing` is a custom no-layout dashboard route

## Backend shape

- FastAPI + SAFRS + SQLite
- bootstrap seeds galleries and statuses
- upload handling is enabled for images

## Rules shape

- LogicBank derives gallery counts and sizes
- LogicBank copies sharing fields from `ShareStatus` to `ImageAsset`
- LogicBank enforces publish-time and numeric constraints

## Singleton versus first-class resource decisions

No singleton/settings resource is used in this example. `Gallery` remains a
first-class CRUD resource because it is user-visible and referenced by many
images.

## Custom pages

- `Home.tsx` for the required in-admin entry page
- `Landing.tsx` for dashboard-style image management summary

## Out-of-scope architectural decisions

- no external object storage
- no multi-tenant site model
- no public end-user frontend
