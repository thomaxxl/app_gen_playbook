import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { Layout, Menu, Title, useGetList } from "react-admin";
import type { LayoutProps, RaRecord } from "react-admin";

import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import PageHeader from "./PageHeader";
import PageHero from "./PageHero";
import SectionBlock from "./SectionBlock";
import SummaryCard from "./SummaryCard";
import { OBSERVER_NAVIGATION_ITEMS } from "./observerRouteContracts";

type ListResult = {
  data?: RaRecord[];
  error?: unknown;
  isLoading?: boolean;
  isPending?: boolean;
  total?: number;
};

type RunRecord = RaRecord & {
  change_id?: string;
  completion_complete?: boolean;
  current_phase_code?: string;
  latest_activity_at?: string;
  latest_activity_source?: string;
  mode?: string;
  overall_progress?: number;
  run_id_raw?: string;
  status?: string;
  title?: string;
};

type PhaseRecord = RaRecord & {
  blocker_count?: number;
  ended_at?: string;
  phase_code?: string;
  progress?: number;
  started_at?: string;
  status?: string;
};

type ArtifactPackageRecord = RaRecord & {
  approved_count?: number;
  blocked_count?: number;
  family?: string;
  overall_status?: string;
  readiness_ratio?: number;
  total_count?: number;
  updated_at?: string;
};

type ArtifactRecord = RaRecord & {
  owner_role_code?: string;
  path?: string;
  phase_code?: string;
  status?: string;
  title?: string;
  updated_at?: string;
};

type MessageRecord = RaRecord & {
  created_at?: string;
  from_role_code?: string;
  gate_status?: string;
  importance?: string;
  message_state?: string;
  notes?: string;
  purpose?: string;
  to_role_code?: string;
  topic?: string;
};

type BlockerRecord = RaRecord & {
  details?: string;
  opened_at?: string;
  phase_code?: string;
  role_code?: string;
  severity?: string;
  state?: string;
  title?: string;
};

type EvidenceRecord = RaRecord & {
  captured_at?: string;
  evidence_type?: string;
  path?: string;
  phase_code?: string;
  role_code?: string;
  state?: string;
  summary?: string;
};

type VerificationRecord = RaRecord & {
  check_name?: string;
  evidence_count?: number;
  missing_evidence?: boolean;
  owner_role_code?: string;
  phase_code?: string;
  status?: string;
};

type WorkerRecord = RaRecord & {
  change_id?: string;
  claimed_at?: string;
  last_heartbeat?: string;
  role_code?: string;
  session_id?: string;
  status?: string;
};

type EventRecord = RaRecord & {
  event_type?: string;
  role_code?: string;
  severity?: string;
  summary_text?: string;
  timestamp?: string;
};

type FileRecord = RaRecord & {
  logical_group?: string;
  modified_at?: string;
  parser_status?: string;
  phase_code?: string;
  relative_path?: string;
  role_code?: string;
  top_level_area?: string;
};

type ChangeRecord = RaRecord & {
  accepted_at?: string;
  change_id?: string;
  created_at?: string;
  current_state?: string;
  requested_mode?: string;
  reason?: string;
};

function isBusy(result: { isLoading?: boolean; isPending?: boolean }) {
  return Boolean(result.isPending ?? result.isLoading);
}

function totalFor(result: ListResult) {
  return result.total ?? result.data?.length ?? 0;
}

function formatValue(value: unknown, fallback = "Unknown") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value).replace(/_/g, " ");
}

function normalizeRunStatus(run: RunRecord | undefined) {
  if (!run) {
    return "unknown";
  }
  if (run.completion_complete) {
    return "completed";
  }
  return formatValue(run.status, "unknown");
}

function renderPageState(title: string, results: ListResult[], children: ReactNode) {
  if (results.some((result) => isBusy(result))) {
    return (
      <SummaryCard title={title}>
        <Typography color="text.secondary" variant="body2">
          Loading observer resources...
        </Typography>
      </SummaryCard>
    );
  }

  const firstError = results.find((result) => result.error)?.error;
  if (firstError) {
    return (
      <ErrorState
        message="The observer page could not complete its data queries."
        title={title}
      />
    );
  }

  return children;
}

function useCurrentRunQuery() {
  const runQuery = useGetList("Run", {
    filter: {},
    pagination: { page: 1, perPage: 5 },
    sort: { field: "latest_activity_at", order: "DESC" },
  });

  const runs = (runQuery.data ?? []) as RunRecord[];
  const currentRun = runs[0];
  const currentRunId = currentRun?.id ?? "__none__";
  return { currentRun, currentRunId, runQuery };
}

export function ObserverMenu() {
  return (
    <Menu>
      {OBSERVER_NAVIGATION_ITEMS.map((item) => (
        <Menu.Item key={item.path} primaryText={item.label} to={item.path} />
      ))}
    </Menu>
  );
}

export function ObserverLayout(props: LayoutProps) {
  return <Layout {...props} menu={ObserverMenu} />;
}

function RunHero({ currentRun }: { currentRun: RunRecord | undefined }) {
  return (
    <PageHero
      description="Live current-run status pulled from the run-dashboard mirror, not from placeholder PM seed data."
      eyebrow="Run observer"
      title={currentRun?.title ?? "Current Run Overview"}
    />
  );
}

export function PhasesPage() {
  const { currentRun, currentRunId, runQuery } = useCurrentRunQuery();
  const phaseQuery = useGetList("RunPhaseStatus", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "phase_code", order: "ASC" },
  });
  const phases = (phaseQuery.data ?? []) as PhaseRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Phases" />
      <PageHeader
        description="Phase completion, progress, and blocker counts come directly from mirrored run phase state."
        title="Phases"
      />
      {renderPageState("Phases", [runQuery, phaseQuery], (
        phases.length === 0 ? (
          <EmptyState message="No phase rows are available for the current run." title="No phases yet" />
        ) : (
          <Grid container spacing={2}>
            {phases.map((phase) => (
              <Grid key={String(phase.id)} size={{ xs: 12, md: 6 }}>
                <SummaryCard title={formatValue(phase.phase_code)}>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      Status: {formatValue(phase.status)}
                    </Typography>
                    <Typography variant="body2">
                      Progress: {String(phase.progress ?? 0)}%
                    </Typography>
                    <Typography variant="body2">
                      Blockers: {String(phase.blocker_count ?? 0)}
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      {phase.focus_summary ?? "No focus summary recorded."}
                    </Typography>
                  </Stack>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
        )
      ))}
      <SummaryCard title="Current run">
        <Typography variant="body2">
          {currentRun?.run_id_raw ?? "No current run detected"}
        </Typography>
      </SummaryCard>
    </Box>
  );
}

export function ArtifactsPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const packageQuery = useGetList("ArtifactPackage", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "family", order: "ASC" },
  });
  const artifactQuery = useGetList("Artifact", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "updated_at", order: "DESC" },
  });
  const packages = (packageQuery.data ?? []) as ArtifactPackageRecord[];
  const artifacts = (artifactQuery.data ?? []) as ArtifactRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Artifacts" />
      <PageHeader
        description="Artifact package readiness and individual artifact status are read from the mirrored run state."
        title="Artifacts"
      />
      {renderPageState("Artifacts", [runQuery, packageQuery, artifactQuery], (
        <>
          <Grid container spacing={2}>
            {packages.map((pkg) => (
              <Grid key={String(pkg.id)} size={{ xs: 12, md: 4 }}>
                <SummaryCard title={pkg.family ?? `Package ${pkg.id}`}>
                  <Typography variant="body2">
                    Status: {formatValue(pkg.overall_status)}
                  </Typography>
                  <Typography variant="body2">
                    Readiness: {String(pkg.readiness_ratio ?? 0)}
                  </Typography>
                  <Typography variant="body2">
                    Approved: {String(pkg.approved_count ?? 0)} / {String(pkg.total_count ?? 0)}
                  </Typography>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
          <SectionBlock
            description="Recent artifact updates stay visible below the package summary."
            title="Recent artifacts"
          >
            {artifacts.length === 0 ? (
              <EmptyState message="No artifact rows are available for the current run." title="No artifacts yet" />
            ) : (
              <List disablePadding>
                {artifacts.map((artifact) => (
                  <ListItem key={String(artifact.id)} divider>
                    <ListItemText
                      primary={artifact.title ?? artifact.path ?? `Artifact ${artifact.id}`}
                      secondary={`${formatValue(artifact.status)} | ${formatValue(artifact.phase_code)} | ${formatValue(artifact.owner_role_code)}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </SectionBlock>
        </>
      ))}
    </Box>
  );
}

export function MessagesPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const messageQuery = useGetList("HandoffMessage", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "created_at", order: "DESC" },
  });
  const messages = (messageQuery.data ?? []) as MessageRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Messages" />
      <PageHeader
        description="Queue messages, handoffs, and operator notes are listed from the mirrored role-state message catalog."
        title="Messages"
      />
      {renderPageState("Messages", [runQuery, messageQuery], (
        messages.length === 0 ? (
          <EmptyState message="No queue messages are available for the current run." title="No messages yet" />
        ) : (
          <Grid container spacing={2}>
            {messages.map((message) => (
              <Grid key={String(message.id)} size={{ xs: 12, md: 6 }}>
                <SummaryCard title={message.topic ?? message.purpose ?? message.id.toString()}>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      {formatValue(message.from_role_code)}
                      {" -> "}
                      {formatValue(message.to_role_code)}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip label={formatValue(message.importance)} size="small" />
                      <Chip label={formatValue(message.message_state)} size="small" />
                      <Chip label={formatValue(message.gate_status)} size="small" />
                    </Stack>
                    <Typography color="text.secondary" variant="body2">
                      {message.purpose ?? "No purpose recorded."}
                    </Typography>
                  </Stack>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
        )
      ))}
    </Box>
  );
}

export function BlockersPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const blockerQuery = useGetList("Blocker", {
    filter: { run_id: currentRunId, state: "open" },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "opened_at", order: "DESC" },
  });
  const blockers = (blockerQuery.data ?? []) as BlockerRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Blockers" />
      <PageHeader
        description="Open blocker rows are taken directly from the mirrored blocker projection."
        title="Blockers"
      />
      {renderPageState("Blockers", [runQuery, blockerQuery], (
        blockers.length === 0 ? (
          <EmptyState message="No open blockers are recorded for the current run." title="No blockers" />
        ) : (
          <Grid container spacing={2}>
            {blockers.map((blocker) => (
              <Grid key={String(blocker.id)} size={{ xs: 12, md: 6 }}>
                <SummaryCard title={blocker.title ?? `Blocker ${blocker.id}`}>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      Severity: {formatValue(blocker.severity)}
                    </Typography>
                    <Typography variant="body2">
                      Phase: {formatValue(blocker.phase_code)} | Owner: {formatValue(blocker.role_code)}
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      {blocker.details ?? "No details recorded."}
                    </Typography>
                  </Stack>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
        )
      ))}
    </Box>
  );
}

export function EvidencePage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const evidenceQuery = useGetList("EvidenceItem", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "captured_at", order: "DESC" },
  });
  const verificationQuery = useGetList("VerificationCheck", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "finished_at", order: "DESC" },
  });
  const evidence = (evidenceQuery.data ?? []) as EvidenceRecord[];
  const checks = (verificationQuery.data ?? []) as VerificationRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Evidence" />
      <PageHeader
        description="Evidence and verification are both listed from the mirrored run evidence projections."
        title="Evidence"
      />
      {renderPageState("Evidence", [runQuery, evidenceQuery, verificationQuery], (
        <>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <SummaryCard title="Evidence items">
                <Typography variant="h4">{String(totalFor(evidenceQuery))}</Typography>
              </SummaryCard>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <SummaryCard title="Verification checks">
                <Typography variant="h4">{String(totalFor(verificationQuery))}</Typography>
              </SummaryCard>
            </Grid>
          </Grid>
          <SectionBlock description="Latest evidence items." title="Recent evidence">
            <List disablePadding>
              {evidence.map((item) => (
                <ListItem key={String(item.id)} divider>
                  <ListItemText
                    primary={item.summary ?? item.path ?? `Evidence ${item.id}`}
                    secondary={`${formatValue(item.evidence_type)} | ${formatValue(item.state)} | ${formatValue(item.phase_code)}`}
                  />
                </ListItem>
              ))}
            </List>
          </SectionBlock>
          <SectionBlock description="Latest verification checks." title="Verification">
            <List disablePadding>
              {checks.map((check) => (
                <ListItem key={String(check.id)} divider>
                  <ListItemText
                    primary={check.check_name ?? `Check ${check.id}`}
                    secondary={`${formatValue(check.status)} | owner ${formatValue(check.owner_role_code)} | evidence ${String(check.evidence_count ?? 0)}`}
                  />
                </ListItem>
              ))}
            </List>
          </SectionBlock>
        </>
      ))}
    </Box>
  );
}

export function WorkersPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const workerQuery = useGetList("WorkerState", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "last_heartbeat", order: "DESC" },
  });
  const workers = (workerQuery.data ?? []) as WorkerRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Workers" />
      <PageHeader
        description="Worker state reflects the mirrored orchestrator worker registry."
        title="Workers"
      />
      {renderPageState("Workers", [runQuery, workerQuery], (
        workers.length === 0 ? (
          <EmptyState message="No worker rows are available for the current run." title="No workers yet" />
        ) : (
          <Grid container spacing={2}>
            {workers.map((worker) => (
              <Grid key={String(worker.id)} size={{ xs: 12, md: 4 }}>
                <SummaryCard title={worker.role_code ?? `Worker ${worker.id}`}>
                  <Typography variant="body2">
                    Status: {formatValue(worker.status)}
                  </Typography>
                  <Typography variant="body2">
                    Last heartbeat: {formatValue(worker.last_heartbeat)}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Change: {worker.change_id ?? "n/a"}
                  </Typography>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
        )
      ))}
    </Box>
  );
}

export function TimelinePage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const eventQuery = useGetList("OrchestratorEvent", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 25 },
    sort: { field: "timestamp", order: "DESC" },
  });
  const events = (eventQuery.data ?? []) as EventRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Timeline" />
      <PageHeader
        description="Recent orchestration activity is read from mirrored orchestrator events."
        title="Timeline"
      />
      {renderPageState("Timeline", [runQuery, eventQuery], (
        events.length === 0 ? (
          <EmptyState message="No orchestrator events are available for the current run." title="No timeline yet" />
        ) : (
          <List disablePadding>
            {events.map((event) => (
              <ListItem key={String(event.id)} divider>
                <ListItemText
                  primary={event.summary_text ?? event.event_type ?? `Event ${event.id}`}
                  secondary={`${formatValue(event.timestamp)} | ${formatValue(event.severity)} | ${formatValue(event.role_code)}`}
                />
              </ListItem>
            ))}
          </List>
        )
      ))}
    </Box>
  );
}

export function FilesPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const fileQuery = useGetList("RunFile", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 25 },
    sort: { field: "modified_at", order: "DESC" },
  });
  const files = (fileQuery.data ?? []) as FileRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Files" />
      <PageHeader
        description="File catalog rows come from the mirrored run file inventory."
        title="Files"
      />
      {renderPageState("Files", [runQuery, fileQuery], (
        files.length === 0 ? (
          <EmptyState message="No run file rows are available for the current run." title="No files yet" />
        ) : (
          <List disablePadding>
            {files.map((file) => (
              <ListItem key={String(file.id)} divider>
                <ListItemText
                  primary={file.relative_path ?? `File ${file.id}`}
                  secondary={`${formatValue(file.top_level_area)} | ${formatValue(file.logical_group)} | ${formatValue(file.parser_status)}`}
                />
              </ListItem>
            ))}
          </List>
        )
      ))}
    </Box>
  );
}

export function ChangesPage() {
  const { currentRunId, runQuery } = useCurrentRunQuery();
  const changeQuery = useGetList("ChangeRequest", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "created_at", order: "DESC" },
  });
  const changes = (changeQuery.data ?? []) as ChangeRecord[];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Changes" />
      <PageHeader
        description="Change packets are taken from the mirrored change-request projection."
        title="Changes"
      />
      {renderPageState("Changes", [runQuery, changeQuery], (
        changes.length === 0 ? (
          <EmptyState message="No change requests are present for the current run." title="No changes" />
        ) : (
          <Grid container spacing={2}>
            {changes.map((change) => (
              <Grid key={String(change.id)} size={{ xs: 12, md: 6 }}>
                <SummaryCard title={change.change_id ?? `Change ${change.id}`}>
                  <Typography variant="body2">
                    State: {formatValue(change.current_state)}
                  </Typography>
                  <Typography variant="body2">
                    Mode: {formatValue(change.requested_mode)}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    {change.reason ?? "No reason recorded."}
                  </Typography>
                </SummaryCard>
              </Grid>
            ))}
          </Grid>
        )
      ))}
    </Box>
  );
}

export default function RunOverviewPage() {
  const { currentRun, currentRunId, runQuery } = useCurrentRunQuery();
  const phaseQuery = useGetList("RunPhaseStatus", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 20 },
    sort: { field: "phase_code", order: "ASC" },
  });
  const packageQuery = useGetList("ArtifactPackage", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "family", order: "ASC" },
  });
  const blockerQuery = useGetList("Blocker", {
    filter: { run_id: currentRunId, state: "open" },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "opened_at", order: "DESC" },
  });
  const messageQuery = useGetList("HandoffMessage", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "created_at", order: "DESC" },
  });
  const verificationQuery = useGetList("VerificationCheck", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "finished_at", order: "DESC" },
  });
  const workerQuery = useGetList("WorkerState", {
    filter: { run_id: currentRunId },
    pagination: { page: 1, perPage: 12 },
    sort: { field: "last_heartbeat", order: "DESC" },
  });

  const packages = (packageQuery.data ?? []) as ArtifactPackageRecord[];
  const phases = (phaseQuery.data ?? []) as PhaseRecord[];
  const messages = (messageQuery.data ?? []) as MessageRecord[];

  return (
    <Box data-primary-route="/phases" sx={{ display: "grid", gap: 3 }}>
      <Title title="Run Overview" />
      <RunHero currentRun={currentRun} />
      {renderPageState("Run Overview", [runQuery, phaseQuery, packageQuery, blockerQuery, messageQuery, verificationQuery, workerQuery], (
        <>
          <Grid container data-testid="entry-proof-strip" spacing={2}>
            <Grid size={{ xs: 12, md: 3 }}>
              <SummaryCard title="Current run">
                <Typography color="primary" sx={{ fontWeight: 700 }} variant="h4">
                  {currentRun?.run_id_raw ?? "n/a"}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Latest mirrored run id.
                </Typography>
              </SummaryCard>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <SummaryCard title="Status">
                <Typography color="primary" sx={{ fontWeight: 700 }} variant="h4">
                  {normalizeRunStatus(currentRun)}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Phase {formatValue(currentRun?.current_phase_code)}
                </Typography>
              </SummaryCard>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <SummaryCard title="Open blockers">
                <Typography color="primary" sx={{ fontWeight: 700 }} variant="h4">
                  {String(totalFor(blockerQuery))}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Mirrored blocker count.
                </Typography>
              </SummaryCard>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <SummaryCard title="Active workers">
                <Typography color="primary" sx={{ fontWeight: 700 }} variant="h4">
                  {String(totalFor(workerQuery))}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Worker rows for the current run.
                </Typography>
              </SummaryCard>
            </Grid>
          </Grid>

          <SectionBlock
            description="Use the mirrored run status as the operator-facing landing surface."
            title="Run status"
          >
            <SummaryCard title="Current observer state">
              <Stack data-testid="entry-purpose" spacing={1}>
                <Typography variant="body2">
                  Title: {currentRun?.title ?? "No title recorded"}
                </Typography>
                <Typography variant="body2">
                  Mode: {formatValue(currentRun?.mode)}
                </Typography>
                <Typography variant="body2">
                  Progress: {String(currentRun?.overall_progress ?? 0)}%
                </Typography>
                <Typography variant="body2">
                  Latest activity: {formatValue(currentRun?.latest_activity_at)}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Source: {currentRun?.latest_activity_source ?? "No activity source recorded."}
                </Typography>
              </Stack>
            </SummaryCard>
          </SectionBlock>

          <SectionBlock
            description="Primary next-step routes are derived from actual mirrored run data."
            title="Operator next actions"
          >
            <Stack data-testid="entry-primary-cta" direction={{ xs: "column", md: "row" }} spacing={1.5}>
              {OBSERVER_NAVIGATION_ITEMS.slice(1, 6).map((item) => (
                <Chip component="a" clickable href={`#/` + item.path.replace(/^\//, "")} key={item.path} label={item.label} variant="outlined" />
              ))}
            </Stack>
          </SectionBlock>

          <SectionBlock
            description="Top phase rows and artifact package summaries remain visible on the overview."
            title="Status slices"
          >
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <SummaryCard title="Phases">
                  <List disablePadding>
                    {phases.slice(0, 6).map((phase) => (
                      <ListItem divider key={String(phase.id)}>
                        <ListItemText
                          primary={formatValue(phase.phase_code)}
                          secondary={`${formatValue(phase.status)} | ${String(phase.progress ?? 0)}% | blockers ${String(phase.blocker_count ?? 0)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </SummaryCard>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <SummaryCard title="Artifact packages">
                  <List disablePadding>
                    {packages.slice(0, 6).map((pkg) => (
                      <ListItem divider key={String(pkg.id)}>
                        <ListItemText
                          primary={pkg.family ?? `Package ${pkg.id}`}
                          secondary={`${formatValue(pkg.overall_status)} | ready ${String(pkg.approved_count ?? 0)} / ${String(pkg.total_count ?? 0)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </SummaryCard>
              </Grid>
            </Grid>
          </SectionBlock>

          <SectionBlock
            description="Recent high-signal messages are visible without leaving the overview."
            title="Recent messages"
          >
            {messages.length === 0 ? (
              <EmptyState message="No messages were mirrored for the current run." title="No messages yet" />
            ) : (
              <List disablePadding>
                {messages.slice(0, 6).map((message) => (
                  <ListItem divider key={String(message.id)}>
                    <ListItemText
                      primary={message.topic ?? message.purpose ?? `Message ${message.id}`}
                      secondary={`${formatValue(message.from_role_code)} -> ${formatValue(message.to_role_code)} | ${formatValue(message.importance)} | ${formatValue(message.message_state)}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </SectionBlock>
        </>
      ))}
    </Box>
  );
}
