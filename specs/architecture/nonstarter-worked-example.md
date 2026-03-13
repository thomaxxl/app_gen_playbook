owner: architect
phase: phase-2-architecture-contract
status: template-reference
depends_on:
  - resource-naming.md
  - ../ux/custom-view-specs.md
unresolved:
  - adapt this worked example to the actual non-starter domain
last_updated_by: playbook

# Non-Starter Worked Example

This file is a generic worked example for a non-starter domain that does not
fit the starter `Collection` / `Item` / `Status` trio.

Use it when the target app needs:

- four or more resources
- multiple references to the same target resource
- a custom landing or dashboard page that joins several resources

## Example domain

This worked example uses a chess tournament domain:

- `Tournament`
- `Player`
- `Round`
- `Pairing`

This is an example only. The run-owned artifact MUST replace it with the
actual domain.

## Resource naming map

The Architect SHOULD treat the following as a concrete naming example:

| Python model | SQL table | admin.yaml key | SAFRS wire type | collection path |
| --- | --- | --- | --- | --- |
| `Tournament` | `tournaments` | `Tournament` | `Tournament` | `/api/Tournament` |
| `Player` | `players` | `Player` | `Player` | `/api/Player` |
| `Round` | `rounds` | `Round` | `Round` | `/api/Round` |
| `Pairing` | `pairings` | `Pairing` | `Pairing` | `/api/Pairing` |

The actual run-owned artifact MUST validate the final SAFRS collection paths
at runtime instead of assuming this table is correct for another domain.

## Multiple-reference example

`Pairing` references `Player` twice:

- `white_player_id -> Player`
- `black_player_id -> Player`

The generated backend and frontend MUST keep those references distinct.

Recommended relationship names:

- `Pairing.white_player`
- `Pairing.black_player`
- `Player.white_pairings`
- `Player.black_pairings`

The generator MUST NOT collapse same-target references into one generic
relationship just because they point to the same resource type.

The corresponding `admin.yaml` attributes SHOULD be explicit:

- `white_player_id`
  - `type: reference`
  - `reference: Player`
  - `label: White Player`
- `black_player_id`
  - `type: reference`
  - `reference: Player`
  - `label: Black Player`

## Relationship example

Recommended example relationship set:

- `Tournament.rounds`
  one-to-many
- `Tournament.players`
  one-to-many
- `Round.tournament`
  many-to-one
- `Round.pairings`
  one-to-many
- `Pairing.round`
  many-to-one
- `Pairing.white_player`
  many-to-one
- `Pairing.black_player`
  many-to-one

The Backend role MUST document the exact relationship names, delete rules, and
nullability in the run-owned relationship map.

## Custom dashboard example

The default no-layout landing page MAY join:

- `Tournament`
  for event name and current round
- `Round`
  for round labels and scheduling
- `Pairing`
  for active boards
- `Player`
  for readable white/black player names

Example row shape for the custom page:

- tournament name
- round label
- board number
- white player name
- black player name
- result or status

This is the minimum shape that proves the playbook can handle:

- several resources on one page
- multiple same-target references
- user-key display instead of raw foreign-key ids

## Template impact

For a domain of this shape, the operator SHOULD expect to replace at least:

- starter resource wrapper files under `templates/app/frontend/generated/resources/`
- starter `Landing.tsx` with a domain-specific dashboard
- starter backend models, bootstrap, and rules with non-starter variants

The non-starter template lane under `../../templates/nonstarter/` SHOULD be
used for those substitutions.
