from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

from contracts.models import PolicyError


@dataclass(frozen=True)
class SdlcRegistry:
    generated_at: str
    lifecycles: dict[str, dict[str, Any]]
    phases: dict[str, dict[str, Any]]
    milestones: dict[str, dict[str, Any]]
    overlays: dict[str, dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "lifecycles": self.lifecycles,
            "phases": self.phases,
            "milestones": self.milestones,
            "overlays": self.overlays,
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise PolicyError(f"expected mapping in {path}")
    return payload


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(payload: dict[str, Any], schema: dict[str, Any], path: Path, base_uri: str | None = None, store: dict[str, Any] | None = None) -> None:
    resolver = None
    if base_uri or store:
      resolver = RefResolver(base_uri=base_uri or "", referrer=schema, store=store or {})
    validator = Draft202012Validator(schema, resolver=resolver)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise PolicyError(f"{path}: schema validation failed at {location}: {first.message}")


def compile_sdlc_registry(repo_root: Path, *, generated_at: str) -> SdlcRegistry:
    policy_root = repo_root / "specs" / "policy"
    schema_root = policy_root / "schema"
    step_schema_path = schema_root / "sdlc-step.schema.json"
    step_schema = _load_schema(step_schema_path)
    store = {
        step_schema_path.as_uri(): step_schema,
        "sdlc-step.schema.json": step_schema,
    }
    phase_schema_path = schema_root / "sdlc-phase.schema.json"
    phase_schema = _load_schema(phase_schema_path)
    lifecycle_schema = _load_schema(schema_root / "sdlc-lifecycle.schema.json")
    milestone_schema = _load_schema(schema_root / "sdlc-milestone.schema.json")

    phases: dict[str, dict[str, Any]] = {}
    for path in sorted((policy_root / "sdlc" / "phases").glob("*.yaml")):
        payload = _load_yaml(path)
        _validate(payload, phase_schema, path, base_uri=phase_schema_path.as_uri(), store=store)
        phase_id = str(payload["id"])
        if phase_id in phases:
            raise PolicyError(f"duplicate SDLC phase id: {phase_id}")
        phases[phase_id] = payload

    lifecycles: dict[str, dict[str, Any]] = {}
    for path in sorted((policy_root / "sdlc" / "lifecycles").glob("*.yaml")):
        payload = _load_yaml(path)
        _validate(payload, lifecycle_schema, path)
        lifecycle_id = str(payload["id"])
        if lifecycle_id in lifecycles:
            raise PolicyError(f"duplicate SDLC lifecycle id: {lifecycle_id}")
        for phase_id in payload.get("phases", []):
            if phase_id not in phases:
                raise PolicyError(f"lifecycle {lifecycle_id} references unknown phase {phase_id}")
        lifecycles[lifecycle_id] = payload

    overlays: dict[str, dict[str, Any]] = {}
    for path in sorted((policy_root / "sdlc" / "overlays").glob("*.yaml")):
        payload = _load_yaml(path)
        overlay_id = str(payload["id"])
        if overlay_id in overlays:
            raise PolicyError(f"duplicate SDLC overlay id: {overlay_id}")
        overlays[overlay_id] = payload

    milestones: dict[str, dict[str, Any]] = {}
    for phase_id, payload in phases.items():
        milestone_id = str(payload.get("exit_milestone") or "")
        if not milestone_id:
            continue
        step_ids = [str(step["id"]) for step in payload.get("steps", [])]
        milestone_payload = {
            "id": milestone_id,
            "title": f"{payload['title']} exit milestone",
            "phase": phase_id,
            "kind": "gate",
            "owners": payload["owners"],
            "achieved_when": {
                "all_steps_pass": step_ids,
                "required_outputs": payload.get("required_outputs", []),
            },
            "blocks_transition": True,
            "unlocks_phases": [
                candidate_id
                for candidate_id, candidate in phases.items()
                if milestone_id in (candidate.get("entry_milestones") or [])
            ],
        }
        _validate(milestone_payload, milestone_schema, policy_root / "sdlc" / "milestones" / f"{milestone_id}.derived.yaml")
        milestones[milestone_id] = milestone_payload

    return SdlcRegistry(
        generated_at=generated_at,
        lifecycles=dict(sorted(lifecycles.items())),
        phases=dict(sorted(phases.items())),
        milestones=dict(sorted(milestones.items())),
        overlays=dict(sorted(overlays.items())),
    )
