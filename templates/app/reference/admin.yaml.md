resources:
  Project:
    endpoint: /api/projects
    label: Projects
    user_key: slug
    menu_order: 10
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      slug:
        type: text
        list: true
        show: true
      name:
        type: text
        list: true
        show: true
      repo_name:
        type: text
        list: true
        show: true
      default_branch:
        type: text
        show: true
      created_at:
        type: datetime
        show: true

  Run:
    endpoint: /api/runs
    label: Runs
    user_key: run_id_raw
    menu_order: 20
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id_raw:
        type: text
        list: true
        show: true
      title:
        type: text
        list: true
        show: true
      status:
        type: text
        list: true
        show: true
      current_phase_code:
        type: text
        list: true
        show: true
      overall_progress:
        type: number
        list: true
        show: true
      completion_complete:
        type: boolean
        list: true
        show: true
      phase5_ready:
        type: boolean
        show: true
      latest_activity_at:
        type: datetime
        list: true
        show: true
      mode:
        type: text
        show: true
      change_id:
        type: text
        show: true
      started_at:
        type: datetime
        show: true
      ended_at:
        type: datetime
        show: true
      status_reason:
        type: text
        show: true

  RunPhaseStatus:
    endpoint: /api/run_phase_status
    label: Phase Status
    user_key: phase_code
    menu_order: 30
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      status:
        type: text
        list: true
        show: true
      progress:
        type: number
        list: true
        show: true
      blocker_count:
        type: number
        list: true
        show: true
      started_at:
        type: datetime
        show: true
      ended_at:
        type: datetime
        show: true
      focus_summary:
        type: text
        show: true

  ArtifactPackage:
    endpoint: /api/artifact_packages
    label: Artifact Packages
    user_key: family
    menu_order: 40
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      family:
        type: text
        list: true
        show: true
      overall_status:
        type: text
        list: true
        show: true
      readiness_ratio:
        type: number
        list: true
        show: true
      total_count:
        type: number
        list: true
        show: true
      approved_count:
        type: number
        list: true
        show: true
      blocked_count:
        type: number
        list: true
        show: true
      updated_at:
        type: datetime
        show: true

  Artifact:
    endpoint: /api/artifacts
    label: Artifacts
    user_key: path
    menu_order: 50
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      path:
        type: text
        list: true
        show: true
      title:
        type: text
        list: true
        show: true
      owner_role_code:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      status:
        type: text
        list: true
        show: true
      artifact_scope:
        type: text
        show: true
      updated_at:
        type: datetime
        show: true

  HandoffMessage:
    endpoint: /api/handoff_messages
    label: Messages
    user_key: filename
    menu_order: 60
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      filename:
        type: text
        list: true
        show: true
      from_role_code:
        type: text
        list: true
        show: true
      to_role_code:
        type: text
        list: true
        show: true
      topic:
        type: text
        list: true
        show: true
      purpose:
        type: text
        list: true
        show: true
      importance:
        type: text
        list: true
        show: true
      gate_status:
        type: text
        list: true
        show: true
      message_state:
        type: text
        list: true
        show: true
      created_at:
        type: datetime
        list: true
        show: true
      processed_at:
        type: datetime
        show: true

  Blocker:
    endpoint: /api/blockers
    label: Blockers
    user_key: title
    menu_order: 70
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      role_code:
        type: text
        list: true
        show: true
      severity:
        type: text
        list: true
        show: true
      title:
        type: text
        list: true
        show: true
      state:
        type: text
        list: true
        show: true
      opened_at:
        type: datetime
        show: true
      details:
        type: text
        show: true

  EvidenceItem:
    endpoint: /api/evidence_items
    label: Evidence
    user_key: path
    menu_order: 80
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      evidence_type:
        type: text
        list: true
        show: true
      path:
        type: text
        list: true
        show: true
      summary:
        type: text
        list: true
        show: true
      role_code:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      state:
        type: text
        list: true
        show: true
      captured_at:
        type: datetime
        show: true

  VerificationCheck:
    endpoint: /api/verification_checks
    label: Verification Checks
    user_key: check_name
    menu_order: 90
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      check_name:
        type: text
        list: true
        show: true
      status:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      owner_role_code:
        type: text
        list: true
        show: true
      missing_evidence:
        type: boolean
        list: true
        show: true
      evidence_count:
        type: number
        list: true
        show: true
      next_step:
        type: text
        show: true

  WorkerState:
    endpoint: /api/orchestrator_worker_states
    label: Workers
    user_key: role_code
    menu_order: 100
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      role_code:
        type: text
        list: true
        show: true
      status:
        type: text
        list: true
        show: true
      change_id:
        type: text
        list: true
        show: true
      claimed_at:
        type: datetime
        list: true
        show: true
      last_heartbeat:
        type: datetime
        list: true
        show: true
      session_id:
        type: text
        show: true

  OrchestratorEvent:
    endpoint: /api/orchestrator_events
    label: Timeline
    user_key: id
    menu_order: 110
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      timestamp:
        type: datetime
        list: true
        show: true
      severity:
        type: text
        list: true
        show: true
      event_type:
        type: text
        list: true
        show: true
      role_code:
        type: text
        list: true
        show: true
      summary_text:
        type: text
        list: true
        show: true

  RunFile:
    endpoint: /api/run_files
    label: Files
    user_key: relative_path
    menu_order: 120
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      relative_path:
        type: text
        list: true
        show: true
      top_level_area:
        type: text
        list: true
        show: true
      logical_group:
        type: text
        list: true
        show: true
      phase_code:
        type: text
        list: true
        show: true
      role_code:
        type: text
        list: true
        show: true
      modified_at:
        type: datetime
        list: true
        show: true
      parser_status:
        type: text
        list: true
        show: true

  ChangeRequest:
    endpoint: /api/change_requests
    label: Change Requests
    user_key: change_id
    menu_order: 130
    attributes:
      id:
        type: text
        readonly: true
        hidden: true
      run_id:
        type: text
        list: true
        show: true
      change_id:
        type: text
        list: true
        show: true
      requested_mode:
        type: text
        list: true
        show: true
      current_state:
        type: text
        list: true
        show: true
      needs_baseline_alignment:
        type: boolean
        list: true
        show: true
      created_at:
        type: datetime
        list: true
        show: true
      accepted_at:
        type: datetime
        show: true
      reason:
        type: text
        show: true
