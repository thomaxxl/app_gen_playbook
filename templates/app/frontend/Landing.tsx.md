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

```tsx
import { Box, Button, CircularProgress, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useDataProvider } from "react-admin";
import { Link as RouterLink } from "react-router-dom";

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
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack spacing={2} sx={{ minHeight: "100vh", p: 4 }}>
        <Typography variant="h4">Starter Overview</Typography>
        <Typography color="error">Failed to load landing data.</Typography>
        <Paper sx={{ p: 2 }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </Paper>
        <Button component={RouterLink} to="/Collection" variant="contained">
          Open Collections
        </Button>
      </Stack>
    );
  }

  if (rows.length === 0) {
    return (
      <Stack spacing={2} sx={{ minHeight: "100vh", p: 4 }}>
        <Typography variant="h4">Starter Overview</Typography>
        <Typography color="text.secondary">No items are available yet.</Typography>
        <Button component={RouterLink} to="/Collection" variant="contained">
          Open Collections
        </Button>
      </Stack>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", p: 4 }}>
      <Box sx={{ mx: "auto", maxWidth: 1100 }}>
        <Stack alignItems="center" direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h4">Starter Overview</Typography>
          <Button component={RouterLink} to="/Collection" variant="contained">
            Open Collections
          </Button>
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
- If the page needs charts or trees, keep those in separate D3 components under
  `components/visualizations/` and feed them prepared data from the landing
  page.
- For a non-starter domain, the implementation MUST derive the actual resource
  names, columns, and summary sections from:
  - `../../../runs/current/artifacts/ux/custom-view-specs.md`
  - `../../../runs/current/artifacts/ux/navigation.md`
  - `../../../runs/current/artifacts/architecture/resource-naming.md`
  - `../../../runs/current/artifacts/product/custom-pages.md`
