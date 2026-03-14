# `frontend/src/CustomDashboard.tsx`

See also:

- [../../../specs/contracts/frontend/custom-views.md](../../../specs/contracts/frontend/custom-views.md)
- [../../../runs/current/artifacts/ux/custom-view-specs.md](../../../runs/current/artifacts/ux/custom-view-specs.md)
- [../../../runs/current/artifacts/architecture/resource-naming.md](../../../runs/current/artifacts/architecture/resource-naming.md)

Use this pattern when the app needs a non-starter custom dashboard or landing
page and the starter `Landing.tsx.md` example is too specific.

This file is a reusable non-starter example, not a required second landing
pattern. `Home.tsx` may itself host the main dashboard content when the run
does not need a separate custom page component.

```tsx
import {
  Box,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useDataProvider } from "react-admin";

import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import PageHeader from "./PageHeader";
import SummaryCard from "./SummaryCard";

type PrimaryRecord = {
  id: string;
  title: string;
  reference_id: string | number | null;
};

type ReferenceRecord = {
  id: string;
  label: string;
};

export default function CustomDashboard() {
  const dataProvider = useDataProvider();
  const [rows, setRows] = useState<PrimaryRecord[]>([]);
  const [references, setReferences] = useState<Record<string, ReferenceRecord>>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const primary = await dataProvider.getList<PrimaryRecord>("PrimaryResource", {
          pagination: { page: 1, perPage: 50 },
          sort: { field: "id", order: "ASC" },
          filter: {},
        });

        const referenceIds = Array.from(
          new Set(primary.data.map((row) => row.reference_id).filter(Boolean)),
        );
        const referenceResult = referenceIds.length
          ? await dataProvider.getMany<ReferenceRecord>("ReferenceResource", {
              ids: referenceIds,
            })
          : { data: [] as ReferenceRecord[] };

        if (!mounted) {
          return;
        }

        setRows(primary.data);
        setReferences(
          Object.fromEntries(
            referenceResult.data.map((record) => [String(record.id), record]),
          ),
        );
        setLoading(false);
      } catch (nextError) {
        if (!mounted) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : String(nextError));
        setLoading(false);
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, [dataProvider]);

  if (loading) {
    return (
      <Stack alignItems="center" justifyContent="center" minHeight="60vh" spacing={2}>
        <CircularProgress />
        <Typography color="text.secondary">Loading dashboard data...</Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <ErrorState
        details={error}
        message="Failed to load the custom dashboard."
        title="Custom dashboard unavailable"
      />
    );
  }

  if (rows.length === 0) {
    return (
      <Box sx={{ display: "grid", gap: 3, p: 4 }}>
        <PageHeader
          description="Replace this starter dashboard with the run-specific overview page defined by the UX artifacts."
          title="Custom Dashboard"
        />
        <EmptyState
          message="No rows are available for this overview yet."
          title="Nothing to summarize"
        />
      </Box>
    );
  }

  return (
    <Box sx={{ display: "grid", gap: 3, p: 4 }}>
      <PageHeader
        description="Replace this starter dashboard with the run-specific overview page defined by the UX artifacts."
        title="Custom Dashboard"
      />
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <SummaryCard title="Primary rows">
          <Typography variant="h4">{rows.length}</Typography>
        </SummaryCard>
      </Stack>
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Primary</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Reference Label</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.title}</TableCell>
                <TableCell>
                  {references[String(row.reference_id)]?.label ?? "-"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
```

Notes:

- Replace `PrimaryResource`, `ReferenceResource`, `title`, `reference_id`, and
  `label` with the names defined by the app-specific UX and architecture
  artifacts.
- Keep this page inside the React-Admin data-provider context.
- Resolve foreign keys into readable labels instead of displaying raw ids.
- This template SHOULD use the shared `PageHeader`, `EmptyState`,
  `ErrorState`, and `SummaryCard` starter shell unless the run-owned UX
  artifacts explicitly replace it.
