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


SQLITE_SUFFIXES = (
    ".sqlite",
    ".sqlite3",
    ".db",
)


def normalize_prompt_path(path: str) -> str:
    normalized = path.strip()
    if normalized.startswith("`") and normalized.endswith("`") and len(normalized) > 1:
        normalized = normalized[1:-1].strip()
    return normalized


def dedupe_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        normalized = normalize_prompt_path(path)
        if normalized in {"", "[]"}:
            continue
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


def packet_skill_paths(packet: dict[str, object]) -> list[str]:
    payload = packet.get("external_reference_payload", {})
    if not isinstance(payload, dict):
        return []
    skills = payload.get("requested_skill_paths", [])
    if not isinstance(skills, list):
        return []
    return dedupe_paths([str(item).strip() for item in skills if str(item).strip()])


def packet_priority_order(packet: dict[str, object]) -> list[str]:
    payload = packet.get("external_reference_payload", {})
    if not isinstance(payload, dict):
        return []
    priority = payload.get("priority_order", [])
    if not isinstance(priority, list):
        return []
    return dedupe_paths([str(item).strip() for item in priority if str(item).strip()])


def packet_external_reference_lines(packet: dict[str, object]) -> list[str]:
    payload = packet.get("external_reference_payload", {})
    if not isinstance(payload, dict):
        return []
    references = payload.get("references", [])
    if not isinstance(references, list):
        return []
    lines: list[str] = []
    for entry in references:
        if not isinstance(entry, dict):
            continue
        source_path = str(entry.get("source_path", "")).strip()
        fidelity = str(entry.get("fidelity", "")).strip()
        if not source_path:
            continue
        if fidelity:
            lines.append(f"{source_path} ({fidelity})")
        else:
            lines.append(source_path)
    return dedupe_paths(lines)


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


def is_sqlite_input_path(path: str) -> bool:
    normalized = normalize_prompt_path(path)
    lowered = normalized.lower()
    return lowered.endswith(SQLITE_SUFFIXES)


def build_sqlite_input_paths(read_paths: list[str]) -> list[str]:
    return dedupe_paths([path for path in read_paths if is_sqlite_input_path(path)])


def build_visible_write_paths(write_paths: list[str], sqlite_input_paths: list[str]) -> list[str]:
    hidden = {normalize_prompt_path(path) for path in sqlite_input_paths}
    visible: list[str] = []
    for path in write_paths:
        normalized = normalize_prompt_path(path)
        if normalized in hidden:
            continue
        visible.append(normalized)
    return dedupe_paths(visible)


def filter_canonical_outputs(canonical_outputs: list[str], sqlite_input_paths: list[str]) -> list[str]:
    hidden = {normalize_prompt_path(path) for path in sqlite_input_paths}
    filtered: list[str] = []
    for path in canonical_outputs:
        normalized = normalize_prompt_path(path)
        if normalized in hidden:
            continue
        filtered.append(normalized)
    return dedupe_paths(filtered)


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
    sqlite_input_paths: list[str],
    forbidden_paths: list[str],
    canonical_outputs: list[str],
    skill_paths: list[str],
    priority_order: list[str],
    external_reference_lines: list[str],
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

    if sqlite_input_paths:
        print("\nSQLite input files (read-only, schema-first):\n")
        for path in sqlite_input_paths:
            print(f"- {path}")
        print(
            "\nSQLite input rules:\n"
            "- inspect the live schema first with `.schema`, `PRAGMA table_info(...)`, or equivalent model metadata before writing SQL\n"
            "- do not assume columns from older runs, prior mirrors, or design notes\n"
            "- treat these SQLite files as read-only inputs for this turn\n"
            "- if you need destructive inspection or transformation tests, copy the DB to scratch space first and leave the listed input unchanged\n"
        )

    if priority_order:
        print("\nPriority order for this turn:\n")
        for value in priority_order:
            print(f"- {value}")

    if skill_paths:
        print("\nRequired skill files:\n")
        for path in skill_paths:
            print(f"- {path}")

    if external_reference_lines:
        print("\nExternal references you MUST follow unless they conflict with the input prompt or business-model contracts:\n")
        for line in external_reference_lines:
            print(f"- {line}")

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
        "- do not write verification shell snippets that fake stdin or hide producer failures; avoid `cmd | python - <<'PY'` and similar broken pipe/heredoc combinations\n"
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
    sqlite_input_paths: list[str],
    forbidden_paths: list[str],
    canonical_outputs: list[str],
    skill_paths: list[str],
    priority_order: list[str],
    external_reference_lines: list[str],
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
    if sqlite_input_paths:
        print("SQLite input files (read-only, schema-first):")
        for path in sqlite_input_paths:
            print(f"- {absolutize(repo_root, path)}")
        print("- Inspect the live schema first with `.schema`, `PRAGMA table_info(...)`, or equivalent model metadata before writing SQL.")
        print("- Do not assume columns from older runs, prior mirrors, or design notes.")
        print("- Treat these SQLite files as read-only inputs; copy to scratch first if destructive testing is required.")
        print("")
    if priority_order:
        print("Priority order:")
        for value in priority_order:
            print(f"- {value}")
        print("")
    if skill_paths:
        print("Required skill files:")
        for path in skill_paths:
            print(f"- {absolutize(repo_root, path) if not path.startswith('.') else path}")
        print("")
    if external_reference_lines:
        print("External references you MUST follow:")
        for line in external_reference_lines:
            print(f"- {line}")
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
    print("- Verification shell snippets must be executable as written; do not use broken pipe/heredoc combinations like `cmd | python - <<'PY'`.")
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
    packet = resolve_read_packet(
        repo_root,
        args.runtime_role,
        message_required_reads=[item for item in sections.get("required reads", []) if isinstance(item, str)],
        explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
        explicit_phase=headers.get("phase"),
        include_message_path=message_path,
    )
    read_paths = dedupe_paths(list(packet["read_paths"]))
    canonical_outputs = build_canonical_outputs(repo_root, args.runtime_role, read_paths, sections)
    write_paths = resolve_writable_paths(
        repo_root,
        args.runtime_role,
        explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
        explicit_phase=headers.get("phase"),
        message_required_reads=[item for item in sections.get("required reads", []) if isinstance(item, str)],
    )
    sqlite_input_paths = build_sqlite_input_paths(read_paths)
    write_paths = build_visible_write_paths(write_paths, sqlite_input_paths)
    canonical_outputs = filter_canonical_outputs(canonical_outputs, sqlite_input_paths)
    read_only_required_paths = build_read_only_required_paths(read_paths, write_paths)
    forbidden_paths = resolve_forbidden_paths(repo_root, args.runtime_role)
    skill_paths = packet_skill_paths(packet)
    priority_order = packet_priority_order(packet)
    external_reference_lines = packet_external_reference_lines(packet)

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
            sqlite_input_paths,
            forbidden_paths,
            canonical_outputs,
            skill_paths,
            priority_order,
            external_reference_lines,
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
            sqlite_input_paths,
            forbidden_paths,
            canonical_outputs,
            skill_paths,
            priority_order,
            external_reference_lines,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
