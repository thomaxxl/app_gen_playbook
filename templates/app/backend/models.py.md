from __future__ import annotations

from safrs import SAFRSBase
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# Declare real SQLAlchemy relationships whenever the domain has a real link.
# Helper endpoints such as `/api/run_project_summary` do not replace
# `Run.project`, `Project.runs`, or the corresponding SAFRS relationship URLs.


class Project(SAFRSBase, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    repo_name: Mapped[str] = mapped_column(String, nullable=False)
    default_branch: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    runs: Mapped[list["Run"]] = relationship(back_populates="project")


class Run(SAFRSBase, Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    source_brief_path: Mapped[str] = mapped_column(String, nullable=False)
    source_root_path: Mapped[str] = mapped_column(String, nullable=False)
    app_root_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    raw_status: Mapped[str | None] = mapped_column(String)
    run_id_raw: Mapped[str] = mapped_column(String, nullable=False)
    change_id: Mapped[str | None] = mapped_column(String)
    current_phase_code: Mapped[str | None] = mapped_column(String)
    overall_progress: Mapped[float | None] = mapped_column(Float)
    phase5_ready: Mapped[bool | None] = mapped_column(Boolean)
    completion_complete: Mapped[bool | None] = mapped_column(Boolean)
    latest_activity_at: Mapped[str | None] = mapped_column(String)
    latest_activity_source: Mapped[str | None] = mapped_column(Text)
    status_reason: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(String)
    ended_at: Mapped[str | None] = mapped_column(String)
    interrupted_at: Mapped[str | None] = mapped_column(String)
    resumed_at: Mapped[str | None] = mapped_column(String)
    project: Mapped["Project"] = relationship(back_populates="runs")
    run_phase_status: Mapped[list["RunPhaseStatus"]] = relationship(back_populates="run")


class RunPhaseStatus(SAFRSBase, Base):
    __tablename__ = "run_phase_status"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    phase_code: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    raw_status: Mapped[str | None] = mapped_column(String)
    started_at: Mapped[str | None] = mapped_column(String)
    ended_at: Mapped[str | None] = mapped_column(String)
    progress: Mapped[float] = mapped_column(Float, nullable=False)
    blocker_count: Mapped[int] = mapped_column(Integer, nullable=False)
    focus_summary: Mapped[str | None] = mapped_column(Text)
    raw_payload_json: Mapped[dict | list | None] = mapped_column(JSON)
    run: Mapped["Run"] = relationship(back_populates="run_phase_status")


class ArtifactPackage(SAFRSBase, Base):
    __tablename__ = "artifact_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    family: Mapped[str] = mapped_column(String, nullable=False)
    root_path: Mapped[str] = mapped_column(String, nullable=False)
    overall_status: Mapped[str] = mapped_column(String, nullable=False)
    readiness_ratio: Mapped[float | None] = mapped_column(Float)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    stub_count: Mapped[int] = mapped_column(Integer, nullable=False)
    draft_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ready_count: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False)
    blocked_count: Mapped[int] = mapped_column(Integer, nullable=False)
    superseded_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class Artifact(SAFRSBase, Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    package_id: Mapped[str | None] = mapped_column(String(36))
    file_id: Mapped[str | None] = mapped_column(String(36))
    path: Mapped[str] = mapped_column(String, nullable=False)
    artifact_scope: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    owner_role_code: Mapped[str] = mapped_column(String, nullable=False)
    phase_code: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    raw_status: Mapped[str | None] = mapped_column(String)
    last_updated_by_role_code: Mapped[str | None] = mapped_column(String)
    unresolved: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON)
    content_hash: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class HandoffMessage(SAFRSBase, Base):
    __tablename__ = "handoff_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(36))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    role_lane: Mapped[str] = mapped_column(String, nullable=False)
    lane_role_code: Mapped[str | None] = mapped_column(String)
    state_dir: Mapped[str] = mapped_column(String, nullable=False)
    message_key: Mapped[str] = mapped_column(String(36), nullable=False)
    message_timestamp: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    from_role_code: Mapped[str | None] = mapped_column(String)
    to_role_code: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str | None] = mapped_column(String)
    purpose: Mapped[str | None] = mapped_column(String)
    importance: Mapped[str] = mapped_column(String, nullable=False)
    requires_dual_validation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    product_manager_validated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    architect_validated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    dual_validation_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    gate_status: Mapped[str] = mapped_column(String, nullable=False)
    message_state: Mapped[str] = mapped_column(String, nullable=False)
    inbox_path: Mapped[str | None] = mapped_column(String)
    processed_path: Mapped[str | None] = mapped_column(String)
    supersedes_message_id: Mapped[str | None] = mapped_column(String(36))
    supersedes_raw: Mapped[str | None] = mapped_column(String)
    supersedes_path: Mapped[str | None] = mapped_column(String)
    required_reads: Mapped[dict | list | None] = mapped_column(JSON)
    requested_outputs: Mapped[dict | list | None] = mapped_column(JSON)
    dependencies: Mapped[dict | list | None] = mapped_column(JSON)
    blocking_issues: Mapped[dict | list | None] = mapped_column(JSON)
    implementation_evidence_json: Mapped[dict | list | None] = mapped_column(JSON)
    raw_metadata_json: Mapped[dict | list | None] = mapped_column(JSON)
    change_id: Mapped[str | None] = mapped_column(String)
    validation_file_id: Mapped[str | None] = mapped_column(String(36))
    snapshot_file_id: Mapped[str | None] = mapped_column(String(36))
    result_file_id: Mapped[str | None] = mapped_column(String(36))
    events_file_id: Mapped[str | None] = mapped_column(String(36))
    notes: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[str | None] = mapped_column(String)


class Blocker(SAFRSBase, Base):
    __tablename__ = "blockers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    phase_code: Mapped[str | None] = mapped_column(String)
    role_code: Mapped[str | None] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    source_file_id: Mapped[str | None] = mapped_column(String(36))
    change_request_id: Mapped[str | None] = mapped_column(String(36))
    severity: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    raw_payload_json: Mapped[dict | list | None] = mapped_column(JSON)
    current_flag: Mapped[bool | None] = mapped_column(Boolean)
    opened_at: Mapped[str | None] = mapped_column(String)
    resolved_at: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, nullable=False)


class EvidenceItem(SAFRSBase, Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(36))
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(String)
    role_code: Mapped[str | None] = mapped_column(String)
    phase_code: Mapped[str | None] = mapped_column(String)
    change_request_id: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, nullable=False)
    render_mode: Mapped[str | None] = mapped_column(String)
    viewer_key: Mapped[str | None] = mapped_column(String)
    captured_at: Mapped[str | None] = mapped_column(String)


class VerificationCheck(SAFRSBase, Base):
    __tablename__ = "verification_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    phase_code: Mapped[str | None] = mapped_column(String)
    role_code: Mapped[str | None] = mapped_column(String)
    owner_role_code: Mapped[str | None] = mapped_column(String)
    source_file_id: Mapped[str | None] = mapped_column(String(36))
    check_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    evidence_item_id: Mapped[str | None] = mapped_column(String(36))
    missing_evidence: Mapped[bool | None] = mapped_column(Boolean)
    next_step: Mapped[str | None] = mapped_column(Text)
    evidence_count: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(String)
    finished_at: Mapped[str | None] = mapped_column(String)


class WorkerState(SAFRSBase, Base):
    __tablename__ = "orchestrator_worker_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_code: Mapped[str] = mapped_column(String, nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(36))
    change_id: Mapped[str | None] = mapped_column(String)
    claimed_at: Mapped[str | None] = mapped_column(String)
    claimed_message: Mapped[str | None] = mapped_column(String)
    last_heartbeat: Mapped[str | None] = mapped_column(String)
    prompt_file_id: Mapped[str | None] = mapped_column(String(36))
    session_id: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    task_id: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[str | None] = mapped_column(String)


class OrchestratorEvent(SAFRSBase, Base):
    __tablename__ = "orchestrator_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(36))
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    role_code: Mapped[str | None] = mapped_column(String)
    message_filename: Mapped[str | None] = mapped_column(String)
    session_id: Mapped[str | None] = mapped_column(String)
    worker_pid: Mapped[int | None] = mapped_column(Integer)
    details_json: Mapped[dict | list | None] = mapped_column(JSON)
    summary_text: Mapped[str | None] = mapped_column(Text)
    raw_line: Mapped[str | None] = mapped_column(Text)


class RunFile(SAFRSBase, Base):
    __tablename__ = "run_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    stem: Mapped[str] = mapped_column(String, nullable=False)
    extension: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    modified_at: Mapped[str | None] = mapped_column(String)
    content_hash: Mapped[str | None] = mapped_column(String)
    top_level_area: Mapped[str | None] = mapped_column(String)
    logical_group: Mapped[str | None] = mapped_column(String)
    logical_subtype: Mapped[str | None] = mapped_column(String)
    render_mode: Mapped[str | None] = mapped_column(String)
    viewer_key: Mapped[str | None] = mapped_column(String)
    role_code: Mapped[str | None] = mapped_column(String)
    phase_code: Mapped[str | None] = mapped_column(String)
    artifact_family: Mapped[str | None] = mapped_column(String)
    change_id: Mapped[str | None] = mapped_column(String)
    queue_state: Mapped[str | None] = mapped_column(String)
    title: Mapped[str | None] = mapped_column(String)
    preview_text: Mapped[str | None] = mapped_column(Text)
    parser_status: Mapped[str] = mapped_column(String, nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[str] = mapped_column(String, nullable=False)
    last_seen_at: Mapped[str] = mapped_column(String, nullable=False)


class ChangeRequest(SAFRSBase, Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    change_id: Mapped[str] = mapped_column(String, nullable=False)
    request_file_id: Mapped[str | None] = mapped_column(String(36))
    classification_file_id: Mapped[str | None] = mapped_column(String(36))
    impact_manifest_file_id: Mapped[str | None] = mapped_column(String(36))
    promotion_file_id: Mapped[str | None] = mapped_column(String(36))
    requested_mode: Mapped[str | None] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(Text)
    affected_domains_json: Mapped[dict | list | None] = mapped_column(JSON)
    needs_baseline_alignment: Mapped[bool | None] = mapped_column(Boolean)
    baseline_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String)
    accepted_at: Mapped[str | None] = mapped_column(String)
    current_state: Mapped[str | None] = mapped_column(String)


class UserStory(SAFRSBase, Base):
    __tablename__ = "user_stories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    story_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str | None] = mapped_column(String)
    priority: Mapped[str | None] = mapped_column(String)
    delivery_class: Mapped[str | None] = mapped_column(String)
    release: Mapped[str | None] = mapped_column(String)
    story_type: Mapped[str | None] = mapped_column(String)
    story_statement: Mapped[str | None] = mapped_column(Text)
    why_priority: Mapped[str | None] = mapped_column(Text)
    independent_test: Mapped[str | None] = mapped_column(Text)
    current_release: Mapped[bool] = mapped_column(Boolean, nullable=False)
    primary_evidence_mode: Mapped[str | None] = mapped_column(String)
    linked_rule_count: Mapped[int] = mapped_column(Integer, nullable=False)
    supporting_surface_count: Mapped[int] = mapped_column(Integer, nullable=False)
    acceptance_scenario_count: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_case_count: Mapped[int] = mapped_column(Integer, nullable=False)
    acceptance_scenarios_json: Mapped[dict | list | None] = mapped_column(JSON)
    edge_cases_json: Mapped[dict | list | None] = mapped_column(JSON)
    detail_sections_json: Mapped[dict | list | None] = mapped_column(JSON)
    source_file_id: Mapped[str | None] = mapped_column(String(36))
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    source_anchor: Mapped[str | None] = mapped_column(String)


class UserStoryTraceability(SAFRSBase, Base):
    __tablename__ = "user_story_traceability"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    story_id: Mapped[str] = mapped_column(String, nullable=False)
    user_story_id: Mapped[str | None] = mapped_column(String(36))
    workflow_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    rule_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    resource_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    page_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    route_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    supporting_surface_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    sample_data_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    acceptance_ids_json: Mapped[dict | list | None] = mapped_column(JSON)
    permission_context: Mapped[str | None] = mapped_column(Text)
    preview_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    qa_live_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    acceptance_owner: Mapped[str | None] = mapped_column(String)
    source_file_id: Mapped[str | None] = mapped_column(String(36))
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    source_anchor: Mapped[str | None] = mapped_column(String)


class BusinessRule(SAFRSBase, Base):
    __tablename__ = "business_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    rule_class: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    plain_language_rule: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String)
    trigger: Mapped[str | None] = mapped_column(Text)
    preconditions: Mapped[str | None] = mapped_column(Text)
    applies_to_json: Mapped[dict | list | None] = mapped_column(JSON)
    valid_outcome: Mapped[str | None] = mapped_column(Text)
    invalid_outcome: Mapped[str | None] = mapped_column(Text)
    user_visible_consequence: Mapped[str | None] = mapped_column(Text)
    backend_enforcement: Mapped[str | None] = mapped_column(String)
    frontend_mirror: Mapped[str | None] = mapped_column(String)
    frontend_mirror_reason: Mapped[str | None] = mapped_column(Text)
    authoritative_error_message: Mapped[str | None] = mapped_column(Text)
    backend_test_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    frontend_test_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    linked_story_count: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_example_count: Mapped[int] = mapped_column(Integer, nullable=False)
    invalid_example_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_file_id: Mapped[str | None] = mapped_column(String(36))
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    source_anchor: Mapped[str | None] = mapped_column(String)


class BusinessRuleExample(SAFRSBase, Base):
    __tablename__ = "business_rule_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    business_rule_id: Mapped[str | None] = mapped_column(String(36))
    example_kind: Mapped[str] = mapped_column(String, nullable=False)
    example_order: Mapped[int] = mapped_column(Integer, nullable=False)
    example_text: Mapped[str] = mapped_column(Text, nullable=False)


class BusinessRuleStoryLink(SAFRSBase, Base):
    __tablename__ = "business_rule_story_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    business_rule_id: Mapped[str | None] = mapped_column(String(36))
    story_id: Mapped[str] = mapped_column(String, nullable=False)
    user_story_id: Mapped[str | None] = mapped_column(String(36))
    story_title: Mapped[str | None] = mapped_column(String)
    story_actor: Mapped[str | None] = mapped_column(String)
    story_priority: Mapped[str | None] = mapped_column(String)


EXPOSED_MODELS = (
    Project,
    Run,
    RunPhaseStatus,
    ArtifactPackage,
    Artifact,
    HandoffMessage,
    Blocker,
    EvidenceItem,
    VerificationCheck,
    WorkerState,
    OrchestratorEvent,
    RunFile,
    ChangeRequest,
    UserStory,
    UserStoryTraceability,
    BusinessRule,
    BusinessRuleExample,
    BusinessRuleStoryLink,
)
