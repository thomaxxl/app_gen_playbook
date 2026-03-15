#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from orchestrator_common import (
    ARTIFACT_AREA_BY_ROLE,
    relpath,
    resolve_repo_root,
)


CORE_READS = (
    "playbook/summaries/global-core.md",
    "playbook/roles/shared-responsibilities.md",
    "playbook/process/inbox-protocol.md",
    "playbook/process/capability-loading.md",
    "playbook/process/ownership-and-edits.md",
    "playbook/process/single-operator-mode.md",
)


SECTION_TITLES = (
    "required reads",
    "requested outputs",
    "dependencies",
    "gate status",
    "blocking issues",
    "notes",
)


def parse_message_sections(message_text: str) -> dict[str, list[str] | str]:
    lines = message_text.splitlines()
    sections: dict[str, list[str]] = {title: [] for title in SECTION_TITLES}
    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        normalized = re.sub(r"^[#\-\*\s]+", "", line).rstrip(":").strip().lower()

        if normalized in SECTION_TITLES:
            current_section = normalized
            continue

        if current_section is None:
            continue

        if not line:
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet_match:
            sections[current_section].append(bullet_match.group(1).strip())
        elif numbered_match:
            sections[current_section].append(numbered_match.group(1).strip())
        else:
            sections[current_section].append(line)

    output: dict[str, list[str] | str] = {}
    for key, values in sections.items():
        cleaned = [value for value in values if value]
        if key == "gate status":
            output[key] = cleaned[0] if cleaned else "unspecified"
        else:
            output[key] = cleaned
    return output


def dedupe_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        normalized = path.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def allowed_write_paths(runtime_role: str) -> list[str]:
    role_dir = f"runs/current/role-state/{runtime_role}/"
    writes = [
        f"runs/current/artifacts/{ARTIFACT_AREA_BY_ROLE[runtime_role]}/**",
        f"{role_dir}context.md",
        f"{role_dir}processed/**",
        "runs/current/evidence/**",
        "runs/current/role-state/*/inbox/*.md",
    ]

    if runtime_role == "product_manager":
        writes.append("app/BUSINESS_RULES.md")
    elif runtime_role == "frontend":
        writes.extend(
            [
                "app/frontend/**",
                "app/reference/admin.yaml",
                "app/README.md",
            ]
        )
    elif runtime_role == "backend":
        writes.extend(
            [
                "app/backend/**",
                "app/reference/admin.yaml",
            ]
        )
    elif runtime_role == "deployment":
        writes.extend(
            [
                "app/Dockerfile",
                "app/docker-compose.yml",
                "app/nginx.conf",
                "app/entrypoint.sh",
                "app/install.sh",
                "app/run.sh",
                "app/README.md",
            ]
        )

    return writes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--display-role", required=True)
    parser.add_argument("--runtime-role", required=True)
    parser.add_argument("--role-file", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    message_path = Path(args.message).resolve()
    role_file = Path(args.role_file)
    message_text = message_path.read_text(encoding="utf-8")
    sections = parse_message_sections(message_text)

    read_paths = list(CORE_READS)
    read_paths.append(role_file.as_posix())
    read_paths.append("runs/current/artifacts/architecture/capability-profile.md")
    read_paths.append("runs/current/artifacts/architecture/load-plan.md")

    role_context = repo_root / "runs" / "current" / "role-state" / args.runtime_role / "context.md"
    if role_context.exists():
        read_paths.append(relpath(role_context, repo_root))

    for item in sections.get("required reads", []):
        if isinstance(item, str):
            read_paths.append(item)

    read_paths.append(relpath(message_path, repo_root))
    read_paths = dedupe_paths(read_paths)

    print(f"You are the {args.display_role} agent for app_gen_playbook.\n")
    print("Process exactly one inbox message:\n")
    print(f"- {relpath(message_path, repo_root)}\n")
    print("Read only these files before acting:\n")
    for path in read_paths:
        print(f"- {path}")

    print("\nAllowed writes:\n")
    for path in allowed_write_paths(args.runtime_role):
        print(f"- {path}")

    print(
        "\nForbidden behavior:\n"
        "- do not process any other inbox item\n"
        "- do not load unrelated role files or feature packs not required by this task\n"
        "- do not edit artifacts owned by another role\n"
        "- do not silently patch playbook contract areas unless the inbox task explicitly delegates playbook maintenance\n"
    )

    print("Current message metadata:\n")
    print(f"- gate status: {sections.get('gate status', 'unspecified')}")
    for title in ("requested outputs", "dependencies", "blocking issues", "notes"):
        values = sections.get(title, [])
        if not values:
            continue
        print(f"- {title}:")
        for value in values:
            print(f"  - {value}")

    print(
        "\nWhen finished:\n"
        "1. update owned artifacts\n"
        "2. update the role context.md\n"
        "3. create any required downstream inbox files\n"
        "4. move the processed inbox item into processed/\n"
        "5. summarize what changed and what remains open\n"
    )

    print("Inbox message content:\n")
    print("```md")
    print(message_text.rstrip())
    print("```")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
