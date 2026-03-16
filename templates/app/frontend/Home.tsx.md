# `frontend/src/Home.tsx`

See also:

- [../../../specs/contracts/frontend/home-and-entry.md](../../../specs/contracts/frontend/home-and-entry.md)
- [../../../runs/current/artifacts/ux/landing-strategy.md](../../../runs/current/artifacts/ux/landing-strategy.md)

Use this file for the standard React-admin `Home` page that appears in the
left sidebar.

```tsx
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import { Title } from "react-admin";
import { Link } from "react-router-dom";

import AppIcon from "./AppIcon";
import { appConfig } from "./config";
import EmptyState from "./EmptyState";
import PageHero from "./PageHero";
import QuickActionCard from "./QuickActionCard";
import { resourcePages } from "./generated/resourcePages";
import SectionBlock from "./SectionBlock";
import SummaryCard from "./SummaryCard";

export default function Home() {
  const starterPattern: "hub" | "dashboard" | "landing" = "hub";
  const primaryRoute = resourcePages[0]?.name
    ? `/${resourcePages[0].name}`
    : null;
  const quickActions = resourcePages
    .slice(0, 3)
    .map((resource) => ({
      actionLabel: `Open ${resource.name}`,
      description: `Browse generated list, show, edit, and create pages for ${resource.name}.`,
      title: resource.name,
      to: `/${resource.name}`,
    }));
  const workflowSteps = [
    "Open the primary resource.",
    "Follow readable relationship labels into related records.",
    "Use show-page tabs to move through the surrounding data context.",
  ];

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Home" />
      <PageHero
        eyebrow="Workspace overview"
        actions={
          primaryRoute ? (
            <Button
              component={Link}
              data-testid="entry-primary-cta"
              startIcon={<AppIcon name="launch" />}
              to={primaryRoute}
              variant="contained"
            >
              Open Primary Resource
            </Button>
          ) : undefined
        }
        description="Use this entry page to understand the workspace, confirm the most important next step, and jump directly into the main workflow."
        title={appConfig.title}
      />

      <Grid container data-testid="entry-proof-strip" spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard title="Primary next step">
            <Typography color="text.secondary" variant="body2">
              Start with the primary resource route, then move into related
              records through the generated relationship links and tabs.
            </Typography>
          </SummaryCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard title="Available resources">
            <Typography color="text.secondary" variant="body2">
              {resourcePages.length > 0
                ? `${resourcePages.length} generated resource page${resourcePages.length === 1 ? "" : "s"} are registered for this app.`
                : "No generated resources are registered yet."}
            </Typography>
          </SummaryCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard title="Relationship workflow">
            <Typography color="text.secondary" variant="body2">
              Generated list and show pages surface readable relationship
              labels, related-record dialogs, and relationship tabs by default.
            </Typography>
          </SummaryCard>
        </Grid>
      </Grid>

      <SectionBlock
        description="Guide users toward the most useful first actions instead of forcing sidebar exploration."
        title="Quick actions"
      >
        {quickActions.length > 0 ? (
          <Grid container spacing={2}>
            {quickActions.map((action) => (
              <Grid key={action.to} size={{ xs: 12, md: 4 }}>
                <QuickActionCard {...action} />
              </Grid>
            ))}
          </Grid>
        ) : (
          <EmptyState
            message="Register at least one resource page so the entry page can expose a concrete next step."
            title="No quick actions yet"
          />
        )}
      </SectionBlock>

      <SectionBlock
        description={
          starterPattern === "dashboard"
            ? "Summarize the main workflow and the current system state."
            : "Keep this section aligned with the run-owned landing strategy."
        }
        title={starterPattern === "landing" ? "How it works" : "What you can do here"}
      >
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <SummaryCard title="How to use it">
              <Typography color="text.secondary" variant="body2">
                Use the sidebar and quick-action surfaces to browse resources,
                follow the primary workflow, and move into related records through
                readable relationship labels and tabs.
              </Typography>
            </SummaryCard>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <SummaryCard title="Workflow at a glance">
              <Box component="ol" sx={{ color: "text.secondary", m: 0, pl: 2 }}>
                {workflowSteps.map((step) => (
                  <Typography component="li" key={step} variant="body2">
                    {step}
                  </Typography>
                ))}
              </Box>
            </SummaryCard>
          </Grid>
        </Grid>
      </SectionBlock>
    </Box>
  );
}
```

Notes:

- This template derives its primary CTA from the first registered resource so
  it does not hard-code a starter route.
- Replace or extend that CTA when `navigation.md` defines a better primary
  route and `landing-strategy.md` defines a richer primary action.
- `Home.tsx` MUST implement the run-owned `landing-strategy.md`.
- `starterPattern` is bootstrap scaffolding, not shippable product behavior.
  For any non-starter-compatible run, the generated app MUST replace it with
  the concrete `landing-strategy.md` choice (`hub`, `dashboard`, or
  `landing`) instead of leaving the template at the default.
- `Home.tsx` MAY remain a simple navigation hub or MAY host the main dashboard
  content directly, depending on `landing-strategy.md` and
  `custom-view-specs.md`.
- `Home.tsx` MUST NOT ship developer-facing contract, recovery, or provisional
  endpoint copy unless the run explicitly approves an operator-facing debug
  entry surface.
- The sidebar icon is supplied by the `Resource` registration in `App.tsx`.
- `Home.tsx` SHOULD use the shared `PageHero`, `SectionBlock`,
  `QuickActionCard`, and `SummaryCard` starter shell unless the run-owned UX
  artifacts explicitly replace it.
- Preserve `data-testid="entry-purpose"`, `data-testid="entry-primary-cta"`,
  and `data-testid="entry-proof-strip"` or document a run-specific
  replacement test hook.
