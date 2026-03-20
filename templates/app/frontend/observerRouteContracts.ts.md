export type ObserverNavigationItem = {
  label: string;
  path: string;
};

export const OBSERVER_NAVIGATION_ITEMS: ObserverNavigationItem[] = [
  { label: "Run Overview", path: "/Home" },
  { label: "Phases", path: "/phases" },
  { label: "Artifacts", path: "/artifacts" },
  { label: "Messages", path: "/messages" },
  { label: "Blockers", path: "/blockers" },
  { label: "Evidence", path: "/evidence" },
  { label: "Workers", path: "/workers" },
  { label: "Timeline", path: "/timeline" },
  { label: "Files", path: "/files" },
  { label: "Changes", path: "/changes" },
];

export const OBSERVER_RESOURCE_PAGES = [
  "Project",
  "Run",
  "RunPhaseStatus",
  "ArtifactPackage",
  "Artifact",
  "HandoffMessage",
  "Blocker",
  "EvidenceItem",
  "VerificationCheck",
  "WorkerState",
  "OrchestratorEvent",
  "RunFile",
  "ChangeRequest",
] as const;
