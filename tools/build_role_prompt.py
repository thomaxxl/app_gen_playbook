#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from orchestrator_common import (
    RUNTIME_TO_DISPLAY,
    canonical_artifacts_for_role_phases,
    path_matches_rule,
    parse_message_headers,
    parse_message_sections,
    phase_name_from_phase_doc,
    relpath,
    resolve_repo_root,
)
from routing_resolver import resolve_forbidden_paths, resolve_read_packet, resolve_writable_paths


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


def repo_relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return relpath(path, repo_root)
    except ValueError:
        return str(path.resolve())


def absolutize(repo_root: Path, path_value: str) -> str:
    if path_value.startswith("/"):
        return path_value
    return str((repo_root / path_value).resolve())


def build_read_paths(
    repo_root: Path,
    runtime_role: str,
    message_path: Path,
    headers: dict[str, str],
    sections: dict[str, list[str] | str],
) -> list[str]:
    required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]
    packet = resolve_read_packet(
        repo_root,
        runtime_role,
        message_required_reads=required_reads,
        explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
        explicit_phase=headers.get("phase"),
        include_message_path=message_path,
    )
    return dedupe_paths(list(packet["read_paths"]))


def build_canonical_outputs(
    repo_root: Path,
    runtime_role: str,
    read_paths: list[str],
    sections: dict[str, list[str] | str],
) -> list[str]:
    outputs: list[str] = []
    phase_names: list[str] = []

    for read_path in read_paths:
        if not read_path.startswith("playbook/task-bundles/") or not read_path.endswith(".yaml"):
            continue
        packet = resolve_read_packet(repo_root, runtime_role, explicit_task_bundle=read_path)
        bundle = packet.get("task_bundle_payload", {})
        if not isinstance(bundle, dict):
            continue
        required_phase = bundle.get("required_phase", [])
        if isinstance(required_phase, str):
            required_phase = [required_phase]
        for phase_doc in required_phase:
            if not isinstance(phase_doc, str):
                continue
            phase_name = phase_name_from_phase_doc(phase_doc)
            if phase_name:
                phase_names.append(phase_name)

    outputs.extend(canonical_artifacts_for_role_phases(repo_root, runtime_role, phase_names))

    for value in sections.get("requested outputs", []):
        if not isinstance(value, str):
            continue
        path_match = re.findall(
            r"(runs/current/artifacts/[A-Za-z0-9_./-]+\.md|runs/current/evidence/[A-Za-z0-9_./-]+\.md|app/[A-Za-z0-9_./-]+)",
            value,
        )
        outputs.extend(path_match)

    return dedupe_paths(outputs)


def build_read_only_required_paths(read_paths: list[str], write_paths: list[str]) -> list[str]:
    read_only: list[str] = []
    for path in read_paths:
        normalized = path.strip()
        if not normalized.startswith(("runs/current/", "app/")):
            continue
        if any(path_matches_rule(normalized, rule) for rule in write_paths):
            continue
        read_only.append(normalized)
    return dedupe_paths(read_only)


def emit_full_prompt(
    repo_root: Path,
    display_role: str,
    runtime_role: str,
    message_text: str,
    message_path: Path,
    sections: dict[str, list[str] | str],
    read_paths: list[str],
    write_paths: list[str],
    read_only_required_paths: list[str],
    forbidden_paths: list[str],
    canonical_outputs: list[str],
) -> None:
    print(f"You are the {display_role} agent for app_gen_playbook.\n")
    print("Process exactly one inbox message:\n")
    print(f"- {repo_relative_or_absolute(message_path, repo_root)}\n")
    print("Read only these files before acting:\n")
    for path in read_paths:
        print(f"- {path}")

    print("\nAllowed writes:\n")
    for path in write_paths:
        print(f"- {path}")

    if read_only_required_paths:
        print("\nRead-only required files:\n")
        for path in read_only_required_paths:
            print(f"- {path}")

    if forbidden_paths:
        print("\nForbidden writes:\n")
        for path in forbidden_paths:
            print(f"- {path}")

    if canonical_outputs:
        print("\nCanonical outputs for this turn:\n")
        for path in canonical_outputs:
            print(f"- {path}")

    print(
        "\nForbidden behavior:\n"
        "- do not process any other inbox item\n"
        "- do not load unrelated role files or feature packs not required by this task\n"
        "- do not edit artifacts owned by another role\n"
        "- do not silently patch playbook contract areas unless the inbox task explicitly delegates playbook maintenance\n"
        "- do not leave background servers, watchers, or helper processes running when you hand off this turn\n"
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
        "2. rewrite the role context.md so it stays compact and keeps only durable context relevant to future turns or future runs\n"
        "3. create any required downstream inbox files\n"
        "4. terminate any processes you started for this turn\n"
        "5. move the claimed inflight work item into processed/\n"
        "6. start the final response with `Summary: ...`\n"
        "7. then summarize what changed and what remains open\n"
    )

    print("Inbox message content:\n")
    print("```md")
    print(message_text.rstrip())
    print("```")


def emit_short_prompt(
    repo_root: Path,
    display_role: str,
    runtime_role: str,
    message_path: Path,
    sections: dict[str, list[str] | str],
    read_paths: list[str],
    write_paths: list[str],
    read_only_required_paths: list[str],
    forbidden_paths: list[str],
    canonical_outputs: list[str],
) -> None:
    print(f"You are the {display_role} runtime worker for app_gen_playbook.")
    print("Process exactly one inbox item in this turn.")
    print("")
    print(f"Inbox message: {absolutize(repo_root, repo_relative_or_absolute(message_path, repo_root))}")
    print(f"Gate status: {sections.get('gate status', 'unspecified')}")
    print("")
    print("Required reads:")
    for path in read_paths:
        print(f"- {absolutize(repo_root, path)}")
    print("")
    print("Allowed writes:")
    for path in write_paths:
        print(f"- {absolutize(repo_root, path)}")
    print("")
    if read_only_required_paths:
        print("Read-only required files:")
        for path in read_only_required_paths:
            print(f"- {absolutize(repo_root, path)}")
        print("")
    if forbidden_paths:
        print("Forbidden writes:")
        for path in forbidden_paths:
            print(f"- {absolutize(repo_root, path)}")
        print("")
    if canonical_outputs:
        print("Canonical outputs:")
        for path in canonical_outputs:
            print(f"- {absolutize(repo_root, path)}")
        print("")
    print("Hard rules:")
    print("- Read only the listed files plus directly referenced files required to complete this inbox item.")
    print("- Do not process any other inbox item.")
    print("- Do not edit another role's artifact area or app subtree.")
    print("- If contract drift exists, write a handoff into the Architect inbox instead of silently patching around it.")
    print("- Do not leave background servers, watchers, or helper processes running after this turn.")
    print("- Rewrite your role context.md so it stays compact and keeps only durable context relevant to future turns or future runs.")
    print("- Terminate any processes you started for this turn.")
    print("- Move the claimed inflight work item into processed/.")
    print("- Start the final response with `Summary: ...` on a single line.")
    print("")

    for title in ("requested outputs", "dependencies", "blocking issues", "notes"):
        values = sections.get(title, [])
        if not values:
            continue
        print(f"{title.title()}:")
        for value in values:
            print(f"- {value}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--runtime-role", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--display-role")
    parser.add_argument("--role-file")
    parser.add_argument("--mode", choices=("full", "short"), default="full")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    message_path = Path(args.message).resolve()
    display_role = args.display_role or RUNTIME_TO_DISPLAY[args.runtime_role]
    message_text = message_path.read_text(encoding="utf-8")
    headers = parse_message_headers(message_text)
    sections = parse_message_sections(message_text, headers=headers)
    read_paths = build_read_paths(repo_root, args.runtime_role, message_path, headers, sections)
    canonical_outputs = build_canonical_outputs(repo_root, args.runtime_role, read_paths, sections)
    write_paths = resolve_writable_paths(
        repo_root,
        args.runtime_role,
        explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
        explicit_phase=headers.get("phase"),
        message_required_reads=[item for item in sections.get("required reads", []) if isinstance(item, str)],
    )
    read_only_required_paths = build_read_only_required_paths(read_paths, write_paths)
    forbidden_paths = resolve_forbidden_paths(repo_root, args.runtime_role)

    if args.mode == "short":
        emit_short_prompt(
            repo_root,
            display_role,
            args.runtime_role,
            message_path,
            sections,
            read_paths,
            write_paths,
            read_only_required_paths,
            forbidden_paths,
            canonical_outputs,
        )
    else:
        emit_full_prompt(
            repo_root,
            display_role,
            args.runtime_role,
            message_text,
            message_path,
            sections,
            read_paths,
            write_paths,
            read_only_required_paths,
            forbidden_paths,
            canonical_outputs,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
