# LogicBank Rule Exception Record

Use this template whenever the backend does **not** implement a rule primarily through the starter declarative subset.

## Rule identity

- Rule ID(s):
- Short rule name:
- Product source:
- Backend owner:

## Business meaning

- What the rule means in plain English:
- Why it matters transactionally:
- Is persisted DB-backed data involved?:
- Classification: schema constraint / transactional rule / transport concern:

## Candidate LogicBank lanes considered

Document each lane considered and why it was accepted or rejected:

- `Rule.copy`:
- `Rule.formula`:
- `Rule.sum`:
- `Rule.count`:
- `Rule.constraint`:
- Declarative chaining:
- Advanced LogicBank pattern(s) considered:
- Natural-language-to-Python translation used? If yes, where was it verified:

## Chosen implementation lane

- Chosen lane:
- File(s):
- Function / event / rule entrypoint:
- Why the starter declarative subset was insufficient:
- Why an upstream advanced LogicBank pattern was insufficient, if applicable:
- Why this replacement lane is safer or more correct than LogicBank here:

Weak arguments that are not acceptable by themselves:

- easier for the endpoint or frontend
- faster to ship
- easier than modeling the rule
- already had a service helper
- simpler to keep it in one route

## Transaction and model scope

- Mapped models involved:
- Mapped relationships involved:
- Target persisted fields:
- Runtime-only fields, if any:
- Session / commit path used:
- Does this stay on the shared ORM transaction path? If not, why:

## API-visible behavior

- Does failure surface through JSON:API / SAFRS?
- Expected HTTP behavior if applicable:
- Error message / detail contract:
- Retry / idempotency notes if applicable:

## Side effects

- External systems touched:
- Why this is safe at the chosen lifecycle point:
- Compensating / rollback expectations:

## Validation evidence

- ORM-path test(s):
- API-path test(s):
- Reparent / delete / status-transition coverage:
- Activation proof:
- Known out-of-contract mutation paths:

## Approval

- Backend approval:
- Architect approval:
- Date:
- Notes:
