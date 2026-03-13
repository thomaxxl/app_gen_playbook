# Backend Verification Fallbacks

This file defines the allowed fallback strategy when the preferred local
HTTP/ASGI verification path is unavailable.

## Preferred order

1. HTTP-style integration tests with `TestClient`
2. alternate ASGI/in-process transport if the primary path is broken
3. the shipped fallback harness in
   `templates/app/backend/test_api_contract_fallback.py.md`
4. direct route-handler or service-layer invocation with explicit session
   management
5. documented manual evidence captured in notes or `context.md`

## Preferred-path gating

- A generated app MAY gate the preferred `TestClient` suite behind an explicit
  environment variable when that path is known to hang or fail on some host
  environments.
- If such gating is used, the default backend verification command set MUST
  execute the fallback harness plus the non-HTTP bootstrap/rules tests without
  additional operator intervention.
- The preferred-path gate variable SHOULD be app-specific, for example
  `MY_APP_ENABLE_TESTCLIENT=1`.

## Fallback rules

- fallback mode is for environment or tooling failure, not convenience
- the agent MUST record which verification path was used
- the agent MUST still verify the critical business behavior
- mutation verification MUST still prove commit/rollback behavior where
  relevant
- fallback verification is not equivalent to a normal green integration suite
  unless the handoff or acceptance note says so explicitly

## Required evidence

When fallback verification is used, record:

- why the preferred path failed
- which fallback path was used
- what exact behavior was still proved
- what remained unverified

Put that evidence in:

- the relevant role `context.md`
- the handoff note
- and, if needed, the integration review or acceptance review

The playbook MUST ship the fallback harness as a real starter test file, not
only as prose guidance.
