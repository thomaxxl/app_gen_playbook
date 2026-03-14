# `frontend/src/Home.tsx`

See also:

- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)

Use this file for the standard React-admin `Home` page that appears in the
left sidebar.

```tsx
import HomeIcon from "@mui/icons-material/Home";
import LaunchIcon from "@mui/icons-material/Launch";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Title } from "react-admin";
import { Link } from "react-router-dom";

import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";

export default function Home() {
  const primaryRoute = resourcePages[0]?.name
    ? `/${resourcePages[0].name}`
    : null;

  return (
    <Card>
      <Title title="Home" />
      <CardContent>
        <Stack spacing={2}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <HomeIcon color="primary" />
            <Typography component="h1" variant="h5">
              {appConfig.title}
            </Typography>
          </Box>

          <Typography variant="body1">
            This generated admin app provides standard React-admin resource
            pages over a SAFRS FastAPI backend. Use the sidebar to browse the
            available resources and open the project-specific views.
          </Typography>

          {primaryRoute ? (
            <Stack direction="row" spacing={2}>
              <Button
                component={Link}
                to={primaryRoute}
                variant="contained"
                startIcon={<LaunchIcon />}
              >
                Open Primary Resource
              </Button>
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
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
