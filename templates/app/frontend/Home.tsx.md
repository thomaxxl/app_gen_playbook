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

export default function Home() {
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

          <Stack direction="row" spacing={2}>
            <Button
              component={Link}
              to="/Landing"
              variant="contained"
              startIcon={<LaunchIcon />}
            >
              Open Landing
            </Button>
            <Button component={Link} to="/Collection" variant="outlined">
              Open First Resource
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
```

Notes:

- Replace `/Collection` with the first meaningful resource route for the app.
- Keep this page simple. It is a basic description and navigation hub, not a
  data-dense dashboard.
- The sidebar icon is supplied by the `Resource` registration in `App.tsx`.
