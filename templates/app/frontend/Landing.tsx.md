# `frontend/src/Landing.tsx`

See also:

- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)
- [../../../specs/contracts/frontend/record-shape.md](../../../specs/contracts/frontend/record-shape.md)
- [../reference/admin.yaml.md](../reference/admin.yaml.md)

Use this pattern when the app needs a route such as `/admin-app/#/Landing` that
uses the React-Admin data provider but should not render the normal admin
chrome.

This file is a starter-domain example for the default `Collection` / `Item` /
`Status` trio. Projects SHOULD adapt or replace it rather than treating it as
a generic generated page.

STARTER-ONLY WARNING:

- non-starter runs MUST NOT copy this file unchanged
- non-starter runs SHOULD omit it entirely unless
  `runs/current/artifacts/ux/custom-view-specs.md` explicitly requires a
  no-layout page

```tsx
import { Box, Button, CircularProgress, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useDataProvider } from "react-admin";
import { Link as RouterLink } from "react-router-dom";

import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import PageHeader from "./PageHeader";
import { resourcePages } from "./generated/resourcePages";
import SummaryCard from "./SummaryCard";

type ItemRecord = {
  id: string;
  title: string;
  status_id: string | number | null;
};

type StatusRecord = {
  id: string;
  label: string;
};

export default function Landing() {
  const dataProvider = useDataProvider();
  const primaryRoute = resourcePages[0]?.name
    ? `/${resourcePages[0].name}`
    : "/Home";
  const [rows, setRows] = useState<ItemRecord[]>([]);
  const [statuses, setStatuses] = useState<Record<string, StatusRecord>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([
      dataProvider.getList<ItemRecord>("Item", {
        pagination: { page: 1, perPage: 50 },
        sort: { field: "id", order: "ASC" },
        filter: {},
      }),
    ]).then(async ([result]) => {
      const statusIds = Array.from(
        new Set(result.data.map((row) => row.status_id).filter(Boolean)),
      );
      const statusResult = statusIds.length
        ? await dataProvider.getMany<StatusRecord>("Status", { ids: statusIds })
        : { data: [] as StatusRecord[] };

      const statusMap = Object.fromEntries(
        statusResult.data.map((status) => [String(status.id), status]),
      );

      if (mounted) {
        setRows(result.data);
        setStatuses(statusMap);
        setLoading(false);
      }
    }).catch((nextError: unknown) => {
      if (mounted) {
        setError(nextError instanceof Error ? nextError.message : String(nextError));
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
    };
  }, [dataProvider]);

  if (loading) {
    return (
      <Stack alignItems="center" justifyContent="center" minHeight="100vh">
        <CircularProgress />
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          Loading starter overview...
        </Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <Box sx={{ minHeight: "100vh", p: { xs: 2, md: 4 } }}>
        <PageHeader
          actions={
            <Button component={RouterLink} to={primaryRoute} variant="contained">
              Open Primary Resource
            </Button>
          }
          description="Starter no-layout overview page rendered inside the React-admin data-provider context."
          title="Starter Overview"
        />
        <ErrorState
          details={error}
          message="Failed to load landing data."
          title="Starter overview unavailable"
        />
      </Box>
    );
  }

  if (rows.length === 0) {
    return (
      <Box sx={{ minHeight: "100vh", p: { xs: 2, md: 4 } }}>
        <PageHeader
          actions={
            <Button component={RouterLink} to={primaryRoute} variant="contained">
              Open Primary Resource
            </Button>
          }
          description="Starter no-layout overview page rendered inside the React-admin data-provider context."
          title="Starter Overview"
        />
        <EmptyState
          action={
            <Button component={RouterLink} to={primaryRoute} variant="contained">
              Open Primary Resource
            </Button>
          }
          message="No items are available yet."
          title="Nothing to show yet"
        />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", p: { xs: 2, md: 4 } }}>
      <Box sx={{ mx: "auto", maxWidth: 1100 }}>
        <PageHeader
          actions={
            <Button component={RouterLink} to={primaryRoute} variant="contained">
              Open Primary Resource
            </Button>
          }
          description="Starter no-layout overview page rendered inside the React-admin data-provider context."
          title="Starter Overview"
        />
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 3 }}>
          <SummaryCard title="Visible items">
            <Typography variant="h4">{rows.length}</Typography>
          </SummaryCard>
        </Stack>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Item</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <Typography fontWeight={600}>{row.title}</Typography>
                  </TableCell>
                  <TableCell>{statuses[String(row.status_id)]?.label ?? "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
}
```

Notes:

- Route wiring belongs in `App.tsx.md`, not in this file.
- Keep the page inside the React-Admin app so it can reuse the same data
  provider and auth context.
- Do not use the default list/show/edit shell for this route.
- Resolve foreign-key ids into related labels or `user_key` values whenever
  possible.
- This template now derives its primary CTA from the first registered resource
  instead of a hard-coded starter route, but it remains starter-only overall.
- This template SHOULD use the shared `PageHeader`, `EmptyState`,
  `ErrorState`, and `SummaryCard` starter shell unless the run-owned UX
  artifacts explicitly replace it.
- If the page needs charts or trees, keep those in separate D3 components under
  `components/visualizations/` and feed them prepared data from the landing
  page.
- For a non-starter domain, the implementation MUST derive the actual resource
  names, columns, and summary sections from:
  - `../../../runs/current/artifacts/ux/custom-view-specs.md`
  - `../../../runs/current/artifacts/ux/navigation.md`
  - `../../../runs/current/artifacts/architecture/resource-naming.md`
  - `../../../runs/current/artifacts/product/custom-pages.md`
