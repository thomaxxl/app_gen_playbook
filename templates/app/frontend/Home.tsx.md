# `frontend/src/Home.tsx`

See also:

- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)

Use this file for the standard React-admin `Home` page that appears in the
left sidebar.

```tsx
import LaunchIcon from "@mui/icons-material/Launch";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Title } from "react-admin";
import { Link } from "react-router-dom";

import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";
import PageHeader from "./PageHeader";
import SummaryCard from "./SummaryCard";

export default function Home() {
  const primaryRoute = resourcePages[0]?.name
    ? `/${resourcePages[0].name}`
    : null;

  return (
    <Box sx={{ display: "grid", gap: 3 }}>
      <Title title="Home" />
      <PageHeader
        actions={primaryRoute ? (
          <Button
            component={Link}
            startIcon={<LaunchIcon />}
            to={primaryRoute}
            variant="contained"
          >
            Open Primary Resource
          </Button>
        ) : undefined}
        description="This generated admin app provides standard React-admin resource pages over a SAFRS FastAPI backend."
        title={appConfig.title}
      />

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <SummaryCard title="How to use it">
          <Typography color="text.secondary" variant="body2">
            Use the sidebar to browse the available resources, open record
            lists, and navigate into project-specific views.
          </Typography>
        </SummaryCard>

        <SummaryCard title="Primary next step">
          <Typography color="text.secondary" variant="body2">
            Start with the primary resource route, then move into related
            records through the generated relationship links and tabs.
          </Typography>
        </SummaryCard>
      </Stack>
    </Box>
  );
}
```

Notes:

- This template derives its primary CTA from the first registered resource so
  it does not hard-code a starter route.
- Replace or extend that CTA when `navigation.md` defines a better primary
  route.
- `Home.tsx` MAY remain a simple navigation hub or MAY host the main dashboard
  content directly, depending on `custom-view-specs.md`.
- The sidebar icon is supplied by the `Resource` registration in `App.tsx`.
- `Home.tsx` SHOULD use the shared `PageHeader` and `SummaryCard` starter
  shell unless the run-owned UX artifacts explicitly replace it.
