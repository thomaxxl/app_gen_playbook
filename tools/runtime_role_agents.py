from __future__ import annotations

from orchestrator_common import RUNTIME_TO_DISPLAY


ROLE_LOCAL_AGENTS_RULES = {
    "product_manager": "escalate missing product intent through the Product artifact set before handing off downstream",
    "architect": "resolve contract drift through architecture artifacts and inbox handoffs before implementation proceeds",
    "frontend": "treat relationship tabs and related-record popups as baseline behavior unless run-owned UX artifacts explicitly override them",
    "backend": "treat backend route discovery and admin.yaml reconciliation as mandatory before claiming frontend stability",
    "qa": "independently validate the delivered app before CEO approval, reopen the owning lanes when real defects remain, and do not silently patch implementation as part of QA",
    "ceo": "perform the mandatory end-of-phase critical review, with explicit UX/UI scrutiny, before any phase can exit; if stalled, inspect the full run state, repair the current blocker even in local playbook runtime files when necessary, validate delivery through scripts/run_playbook.sh --ceo-delivery-validate before final approval, and record durable playbook/process feedback in owned notes or evidence so the orchestrator can curate runs/current/remarks.md",
    "deployment": "do not change application semantics while implementing packaging or runtime normalization",
}


def role_agents_content(runtime_role: str) -> str:
    display_role = RUNTIME_TO_DISPLAY[runtime_role]
    role_rule = ROLE_LOCAL_AGENTS_RULES[runtime_role]
    return (
        "# AGENTS.md\n\n"
        "These instructions apply to this runtime role directory.\n\n"
        f"- You are the {display_role} runtime worker.\n"
        "- Process exactly one inbox message per noninteractive Codex run.\n"
        "- Claimed work is moved into `inflight/` before you start.\n"
        "- Rewrite `context.md` before finishing the inbox item, keeping only compact durable context relevant to future turns or future runs.\n"
        "- Move the completed inflight item into `processed/`.\n"
        "- Create downstream inbox files when handoff is required.\n"
        "- Do not silently edit another role's owned artifact area or app subtree.\n"
        f"- {role_rule}.\n"
    )
