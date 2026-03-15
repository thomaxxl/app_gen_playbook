import DnsRoundedIcon from "@mui/icons-material/DnsRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import ShieldRoundedIcon from "@mui/icons-material/ShieldRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useDataProvider } from "react-admin";
import { Link as RouterLink } from "react-router-dom";

type ConfigurationItemRecord = {
  ci_class: string;
  environment: string;
  hostname: string;
  id: string;
  ip_address: string;
  is_operational: boolean;
  last_verified_at: string | null;
  name: string;
  operational_value: number;
  risk_score: number;
  service_id: string | number | null;
  status_code: string;
  status_id: string | number | null;
};

type ServiceRecord = {
  code: string;
  ci_count: number;
  id: string;
  name: string;
  owner_name: string;
  operational_ci_count: number;
  total_risk_score: number;
};

type OperationalStatusRecord = {
  code: string;
  id: string;
  is_operational: boolean;
  label: string;
  operational_value: number;
};

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatCoverage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function toneForStatus(isOperational: boolean): string {
  return isOperational ? "rgba(21, 128, 61, 0.12)" : "rgba(217, 119, 6, 0.14)";
}

function StatCard({
  icon,
  label,
  tone,
  value,
}: {
  icon: ReactNode;
  label: string;
  tone: string;
  value: string;
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        background: tone,
        border: "1px solid rgba(15, 23, 42, 0.08)",
        borderRadius: 4,
        p: 2.5,
      }}
    >
      <Stack direction="row" justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography color="text.secondary" variant="body2">
            {label}
          </Typography>
          <Typography
            sx={{
              color: "#0f172a",
              fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
              fontWeight: 700,
            }}
            variant="h4"
          >
            {value}
          </Typography>
        </Stack>
        <Box
          sx={{
            alignItems: "center",
            background: "rgba(255,255,255,0.82)",
            borderRadius: 3,
            color: "#0f172a",
            display: "flex",
            height: 48,
            justifyContent: "center",
            width: 48,
          }}
        >
          {icon}
        </Box>
      </Stack>
    </Paper>
  );
}

export default function Landing() {
  const dataProvider = useDataProvider();
  const [items, setItems] = useState<ConfigurationItemRecord[]>([]);
  const [services, setServices] = useState<ServiceRecord[]>([]);
  const [statuses, setStatuses] = useState<OperationalStatusRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([
      dataProvider.getList<ConfigurationItemRecord>("ConfigurationItem", {
        pagination: { page: 1, perPage: 50 },
        sort: { field: "risk_score", order: "DESC" },
        filter: {},
      }),
      dataProvider.getList<ServiceRecord>("Service", {
        pagination: { page: 1, perPage: 20 },
        sort: { field: "total_risk_score", order: "DESC" },
        filter: {},
      }),
      dataProvider.getList<OperationalStatusRecord>("OperationalStatus", {
        pagination: { page: 1, perPage: 20 },
        sort: { field: "label", order: "ASC" },
        filter: {},
      }),
    ])
      .then(([itemResult, serviceResult, statusResult]) => {
        if (!mounted) {
          return;
        }

        setItems(itemResult.data);
        setServices(serviceResult.data);
        setStatuses(statusResult.data);
        setLoading(false);
      })
      .catch((nextError: unknown) => {
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
      <Stack
        alignItems="center"
        justifyContent="center"
        spacing={2}
        sx={{
          background:
            "radial-gradient(circle at top left, #f7f4d6 0%, #cde6dd 28%, #b8d8f8 60%, #f3f6fb 100%)",
          minHeight: "100vh",
          p: 4,
        }}
      >
        <CircularProgress />
        <Typography variant="h6">Loading the CMDB control room...</Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "radial-gradient(circle at top left, #f7f4d6 0%, #cde6dd 28%, #b8d8f8 60%, #f3f6fb 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography
          sx={{
            fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
            fontWeight: 700,
          }}
          variant="h3"
        >
          Dashboard unavailable
        </Typography>
        <Typography color="error" variant="body1">
          Failed to load CMDB data.
        </Typography>
        <Paper sx={{ p: 2 }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </Paper>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/ConfigurationItem" variant="contained">
            Open Items
          </Button>
          <Button component={RouterLink} to="/Service" variant="outlined">
            Open Services
          </Button>
        </Stack>
      </Stack>
    );
  }

  if (items.length === 0) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "radial-gradient(circle at top left, #f7f4d6 0%, #cde6dd 28%, #b8d8f8 60%, #f3f6fb 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography
          sx={{
            fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
            fontWeight: 700,
          }}
          variant="h3"
        >
          CMDB Control Room
        </Typography>
        <Typography maxWidth={720} variant="body1">
          No configuration items are available yet. Seed data is expected to
          create the first dashboard snapshot automatically.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/ConfigurationItem" variant="contained">
            Open Items
          </Button>
          <Button component={RouterLink} to="/Service" variant="outlined">
            Open Services
          </Button>
        </Stack>
      </Stack>
    );
  }

  const productionItems = items.filter((item) => item.environment === "production");
  const operationalItems = items.filter((item) => item.is_operational).length;
  const coverage = items.length ? operationalItems / items.length : 0;
  const unverifiedItems = items.filter((item) => !item.last_verified_at).length;
  const highestRiskItems = [...items]
    .sort((left, right) => right.risk_score - left.risk_score)
    .slice(0, 5);

  return (
    <Box
      sx={{
        background:
          "radial-gradient(circle at top left, #f7f4d6 0%, #cde6dd 28%, #b8d8f8 60%, #f3f6fb 100%)",
        minHeight: "100vh",
        p: { xs: 3, md: 5 },
      }}
    >
      <Stack spacing={3}>
        <Stack spacing={1.5}>
          <Chip
            label="CMDB control room"
            sx={{
              alignSelf: "flex-start",
              backgroundColor: "rgba(255,255,255,0.8)",
              fontWeight: 700,
            }}
          />
          <Typography
            sx={{
              color: "#0f172a",
              fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
              fontWeight: 700,
            }}
            variant="h3"
          >
            CMDB Operations Console
          </Typography>
          <Typography maxWidth={940} variant="body1">
            Monitor service posture, verification coverage, and the highest-risk
            configuration items across the seeded estate. The generated CRUD
            pages remain the system of record; this landing view summarizes the
            current state.
          </Typography>
        </Stack>

        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <Button component={RouterLink} to="/ConfigurationItem" variant="contained">
            Open Configuration Items
          </Button>
          <Button component={RouterLink} to="/Service" variant="outlined">
            Open Services
          </Button>
          <Button component={RouterLink} to="/OperationalStatus" variant="text">
            Open Statuses
          </Button>
        </Stack>

        <Stack direction={{ xs: "column", lg: "row" }} spacing={2}>
          <Box sx={{ flex: 1 }}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <Box sx={{ flex: 1 }}>
                <StatCard
                  icon={<DnsRoundedIcon />}
                  label="Configuration Items"
                  tone="rgba(255, 255, 255, 0.82)"
                  value={String(items.length)}
                />
              </Box>
              <Box sx={{ flex: 1 }}>
                <StatCard
                  icon={<WarningAmberRoundedIcon />}
                  label="Production Items"
                  tone="rgba(255, 255, 255, 0.82)"
                  value={String(productionItems.length)}
                />
              </Box>
            </Stack>

            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mt: 2 }}>
              <Box sx={{ flex: 1 }}>
                <StatCard
                  icon={<HubRoundedIcon />}
                  label="Operational Coverage"
                  tone="rgba(255, 255, 255, 0.82)"
                  value={formatCoverage(coverage)}
                />
              </Box>
              <Box sx={{ flex: 1 }}>
                <StatCard
                  icon={<ShieldRoundedIcon />}
                  label="Unverified Items"
                  tone="rgba(255, 255, 255, 0.82)"
                  value={String(unverifiedItems)}
                />
              </Box>
            </Stack>
          </Box>

          <Paper
            elevation={0}
            sx={{
              border: "1px solid rgba(15, 23, 42, 0.08)",
              borderRadius: 4,
              minWidth: { lg: 320 },
              p: 2.5,
            }}
          >
            <Stack spacing={1.5}>
              <Typography fontWeight={700} variant="h6">
                Status Reference
              </Typography>
              {statuses.map((status) => (
                <Paper
                  elevation={0}
                  key={status.id}
                  sx={{
                    background: toneForStatus(status.is_operational),
                    borderRadius: 3,
                    p: 1.5,
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" spacing={2}>
                    <Box>
                      <Typography fontWeight={700} variant="body2">
                        {status.label}
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        `{status.code}` copies to child items
                      </Typography>
                    </Box>
                    <Chip
                      label={status.is_operational ? "Operational" : "Non-operational"}
                      size="small"
                    />
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Paper>
        </Stack>

        <Stack direction={{ xs: "column", xl: "row" }} spacing={2}>
          <Paper
            elevation={0}
            sx={{
              border: "1px solid rgba(15, 23, 42, 0.08)",
              borderRadius: 4,
              flex: 1.3,
              overflow: "hidden",
            }}
          >
            <Stack direction="row" justifyContent="space-between" sx={{ p: 2.5 }}>
              <Typography fontWeight={700} variant="h6">
                Highest-Risk Configuration Items
              </Typography>
              <Button component={RouterLink} to="/ConfigurationItem" variant="text">
                Open Items
              </Button>
            </Stack>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Hostname</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Environment</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Risk</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Verified</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {highestRiskItems.map((item) => (
                    <TableRow hover key={item.id}>
                      <TableCell>
                        <Typography fontWeight={600} variant="body2">
                          {item.hostname}
                        </Typography>
                      </TableCell>
                      <TableCell>{item.environment}</TableCell>
                      <TableCell>
                        <Chip label={item.status_code} size="small" />
                      </TableCell>
                      <TableCell>{item.risk_score.toFixed(1)}</TableCell>
                      <TableCell>{formatTimestamp(item.last_verified_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper
            elevation={0}
            sx={{
              border: "1px solid rgba(15, 23, 42, 0.08)",
              borderRadius: 4,
              flex: 1,
              overflow: "hidden",
            }}
          >
            <Stack direction="row" justifyContent="space-between" sx={{ p: 2.5 }}>
              <Typography fontWeight={700} variant="h6">
                Service Posture
              </Typography>
              <Button component={RouterLink} to="/Service" variant="text">
                Open Services
              </Button>
            </Stack>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Service</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Owner</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Coverage</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Risk</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {services.map((service) => (
                    <TableRow hover key={service.id}>
                      <TableCell>
                        <Stack spacing={0.25}>
                          <Typography fontWeight={600} variant="body2">
                            {service.name}
                          </Typography>
                          <Typography color="text.secondary" variant="caption">
                            {service.code}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{service.owner_name}</TableCell>
                      <TableCell>
                        {formatCoverage(
                          service.ci_count ? service.operational_ci_count / service.ci_count : 0,
                        )}
                      </TableCell>
                      <TableCell>{service.total_risk_score.toFixed(1)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Stack>
      </Stack>
    </Box>
  );
}
