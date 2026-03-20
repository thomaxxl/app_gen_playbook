from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class PolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyRegistry:
    generated_at: str
    requirements: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    requirement_sets: dict[str, dict[str, Any]]
    validators: dict[str, dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "requirements": self.requirements,
            "profiles": self.profiles,
            "requirement_sets": self.requirement_sets,
            "validators": self.validators,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise PolicyError(f"expected mapping in {path}")
    return payload


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_schema(payload: dict[str, Any], schema: dict[str, Any], path: Path) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    if not errors:
        return
    first = errors[0]
    location = ".".join(str(part) for part in first.absolute_path) or "<root>"
    raise PolicyError(f"{path}: schema validation failed at {location}: {first.message}")


def ensure_paths_exist(repo_root: Path, requirement: dict[str, Any]) -> None:
    for doc in requirement.get("source_docs", []):
        if not (repo_root / doc).exists():
            raise PolicyError(f"{requirement['id']}: missing source doc {doc}")
    validator_path = requirement["validator"]["entrypoint"]
    if not (repo_root / validator_path).exists():
        raise PolicyError(f"{requirement['id']}: missing validator entrypoint {validator_path}")


def compile_registry(repo_root: Path) -> PolicyRegistry:
    policy_root = repo_root / "specs" / "policy"
    requirement_schema = load_schema(policy_root / "schema" / "requirement.schema.json")
    profile_schema = load_schema(policy_root / "schema" / "profile.schema.json")
    validator_registry_schema = load_schema(policy_root / "schema" / "validator-registry.schema.json")
    attestation_schema_path = policy_root / "schema" / "attestation.schema.json"
    waiver_schema_path = policy_root / "schema" / "waiver.schema.json"

    requirements: dict[str, dict[str, Any]] = {}
    requirement_sets: dict[str, dict[str, Any]] = {}
    for path in sorted((policy_root / "requirements").glob("*.yaml")):
        payload = load_yaml(path)
        validate_against_schema(payload, requirement_schema, path)
        set_id = str(payload["id"])
        if set_id in requirement_sets:
            raise PolicyError(f"duplicate requirement-set id: {set_id}")
        requirement_sets[set_id] = payload
        for requirement in payload["requirements"]:
            requirement_id = str(requirement["id"])
            if requirement_id in requirements:
                raise PolicyError(f"duplicate requirement id: {requirement_id}")
            ensure_paths_exist(repo_root, requirement)
            requirements[requirement_id] = dict(requirement)

    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted((policy_root / "profiles").glob("*.yaml")):
        payload = load_yaml(path)
        validate_against_schema(payload, profile_schema, path)
        profile_id = str(payload["id"])
        if profile_id in profiles:
            raise PolicyError(f"duplicate profile id: {profile_id}")
        profiles[profile_id] = payload

    for profile_id, payload in profiles.items():
        for included in payload.get("includes", []):
            if included not in profiles:
                raise PolicyError(f"profile {profile_id} includes unknown profile {included}")
        for requirement_id in payload.get("requirement_ids", []):
            if requirement_id not in requirements:
                raise PolicyError(
                    f"profile {profile_id} references unknown requirement {requirement_id}"
                )

    validators_path = policy_root / "validators" / "registry.yaml"
    validators: dict[str, dict[str, Any]] = {}
    if validators_path.exists():
        payload = load_yaml(validators_path)
        validate_against_schema(payload, validator_registry_schema, validators_path)
        validators = {str(entrypoint): dict(config) for entrypoint, config in (payload.get("validators") or {}).items()}

    for requirement_id, requirement in requirements.items():
        entrypoint = str(requirement["validator"]["entrypoint"])
        if entrypoint not in validators:
            raise PolicyError(f"requirement {requirement_id} references unregistered validator {entrypoint}")

    referenced_requirement_ids: set[str] = set()
    for payload in profiles.values():
        referenced_requirement_ids.update(str(requirement_id) for requirement_id in payload.get("requirement_ids", []))
    for requirement_id, requirement in requirements.items():
        if requirement_id not in referenced_requirement_ids:
            raise PolicyError(f"requirement {requirement_id} has no activation path through any profile")
        applies_when = requirement.get("applies_when") or {}
        family = str(requirement.get("family", ""))
        if family.startswith("gate-"):
            if not (applies_when.get("gates") or []):
                raise PolicyError(f"gate requirement {requirement_id} must declare applies_when.gates")
            if not (applies_when.get("phases") or []):
                raise PolicyError(f"gate requirement {requirement_id} must declare applies_when.phases")
            if not (applies_when.get("roles") or []):
                raise PolicyError(f"gate requirement {requirement_id} must declare applies_when.roles")
        if requirement.get("manual_attestation", {}).get("required") and not attestation_schema_path.exists():
            raise PolicyError(f"requirement {requirement_id} requires manual attestation but attestation schema is missing")
        if requirement.get("exceptions", {}).get("allowed") and not waiver_schema_path.exists():
            raise PolicyError(f"requirement {requirement_id} allows waivers but waiver schema is missing")

    return PolicyRegistry(
        generated_at=utc_now(),
        requirements=dict(sorted(requirements.items())),
        profiles=dict(sorted(profiles.items())),
        requirement_sets=dict(sorted(requirement_sets.items())),
        validators=dict(sorted(validators.items())),
    )


def write_compiled_registry(repo_root: Path, registry: PolicyRegistry, output_path: Path | None = None) -> Path:
    if output_path is None:
        output_path = repo_root / "specs" / "policy" / "compiled" / "policy-registry.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry.to_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def load_compiled_registry(path: Path) -> PolicyRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PolicyRegistry(
        generated_at=str(payload["generated_at"]),
        requirements=dict(payload["requirements"]),
        profiles=dict(payload["profiles"]),
        requirement_sets=dict(payload.get("requirement_sets", {})),
        validators=dict(payload.get("validators", {})),
    )
