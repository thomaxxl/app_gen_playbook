import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import ConnectingAirportsRoundedIcon from "@mui/icons-material/ConnectingAirportsRounded";
import FlightTakeoffRoundedIcon from "@mui/icons-material/FlightTakeoffRounded";
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

type FlightRecord = {
  id: string;
  actual_departure: string | null;
  delay_minutes: number;
  destination: string;
  flight_number: string;
  gate_id: string | number | null;
  is_departed: boolean;
  scheduled_departure: string;
  status_id: string | number | null;
};

type GateRecord = {
  id: string;
  code: string;
  flight_count: number;
  terminal: string;
  total_delay_minutes: number;
};

type FlightStatusRecord = {
  id: string;
  label: string;
};

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
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
          <Typography sx={{ color: "#0f172a", fontWeight: 800 }} variant="h4">
            {value}
          </Typography>
        </Stack>
        <Box
          sx={{
            alignItems: "center",
            background: "rgba(255,255,255,0.8)",
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
  const [flights, setFlights] = useState<FlightRecord[]>([]);
  const [gates, setGates] = useState<GateRecord[]>([]);
  const [statuses, setStatuses] = useState<Record<string, FlightStatusRecord>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([
      dataProvider.getList<FlightRecord>("Flight", {
        pagination: { page: 1, perPage: 50 },
        sort: { field: "scheduled_departure", order: "ASC" },
        filter: {},
      }),
      dataProvider.getList<GateRecord>("Gate", {
        pagination: { page: 1, perPage: 20 },
        sort: { field: "code", order: "ASC" },
        filter: {},
      }),
    ])
      .then(async ([flightResult, gateResult]) => {
        const statusIds = Array.from(
          new Set(
            flightResult.data
              .map((row) => row.status_id)
              .filter((value): value is string | number => value != null),
          ),
        );
        const statusResult = statusIds.length
          ? await dataProvider.getMany<FlightStatusRecord>("FlightStatus", {
              ids: statusIds.map(String),
            })
          : { data: [] as FlightStatusRecord[] };

        if (!mounted) {
          return;
        }

        setFlights(flightResult.data);
        setGates(gateResult.data);
        setStatuses(
          Object.fromEntries(
            statusResult.data.map((status) => [String(status.id), status]),
          ),
        );
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
            "linear-gradient(135deg, #f7efe5 0%, #dbeafe 55%, #fef3c7 100%)",
          minHeight: "100vh",
          p: 4,
        }}
      >
        <CircularProgress />
        <Typography variant="h6">Loading departure operations board...</Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "linear-gradient(135deg, #f7efe5 0%, #dbeafe 55%, #fef3c7 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography sx={{ fontWeight: 800 }} variant="h3">
          Landing error
        </Typography>
        <Typography color="error" variant="body1">
          Failed to load airport operations data.
        </Typography>
        <Paper sx={{ p: 2 }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </Paper>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/Flight" variant="contained">
            Open Flights
          </Button>
          <Button component={RouterLink} to="/Gate" variant="outlined">
            Open Gates
          </Button>
        </Stack>
      </Stack>
    );
  }

  if (flights.length === 0) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "linear-gradient(135deg, #f7efe5 0%, #dbeafe 55%, #fef3c7 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography sx={{ fontWeight: 800 }} variant="h3">
          Departure Operations
        </Typography>
        <Typography color="text.secondary">
          No flights are available for the current operating window.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/Flight" variant="contained">
            Create Flight
          </Button>
          <Button component={RouterLink} to="/Gate" variant="outlined">
            Review Gates
          </Button>
        </Stack>
      </Stack>
    );
  }

  const delayedFlights = flights.filter((flight) => flight.delay_minutes > 0);
  const departedFlights = flights.filter((flight) => flight.is_departed);
  const totalDelayMinutes = flights.reduce(
    (sum, flight) => sum + (flight.delay_minutes || 0),
    0,
  );
  const busiestGate = [...gates].sort((left, right) => {
    if (right.flight_count !== left.flight_count) {
      return right.flight_count - left.flight_count;
    }
    return right.total_delay_minutes - left.total_delay_minutes;
  })[0];

  const gateLookup = Object.fromEntries(gates.map((gate) => [String(gate.id), gate]));

  return (
    <Box
      sx={{
        background:
          "linear-gradient(135deg, #f7efe5 0%, #dbeafe 55%, #fef3c7 100%)",
        minHeight: "100vh",
        p: { xs: 2, md: 4 },
      }}
    >
      <Box sx={{ margin: "0 auto", maxWidth: 1240 }}>
        <Paper
          elevation={0}
          sx={{
            background:
              "linear-gradient(130deg, rgba(15,23,42,0.96) 0%, rgba(30,64,175,0.92) 58%, rgba(180,83,9,0.88) 100%)",
            borderRadius: 5,
            color: "#f8fafc",
            overflow: "hidden",
            p: { xs: 3, md: 4 },
          }}
        >
          <Stack
            direction={{ xs: "column", md: "row" }}
            justifyContent="space-between"
            spacing={3}
          >
            <Stack spacing={1.5}>
              <Typography
                sx={{ fontSize: { xs: "2rem", md: "3rem" }, fontWeight: 900 }}
              >
                Departure Operations
              </Typography>
              <Typography sx={{ maxWidth: 760, opacity: 0.86 }} variant="h6">
                Live operational snapshot for gates, delays, and outbound
                departures at the airport.
              </Typography>
              <Stack direction="row" flexWrap="wrap" gap={1}>
                <Chip
                  label={`${flights.length} active flight records`}
                  sx={{
                    backgroundColor: "rgba(248,250,252,0.15)",
                    color: "#f8fafc",
                    fontWeight: 700,
                  }}
                />
                <Chip
                  label={`${gates.length} gates tracked`}
                  sx={{
                    backgroundColor: "rgba(248,250,252,0.15)",
                    color: "#f8fafc",
                    fontWeight: 700,
                  }}
                />
              </Stack>
            </Stack>
            <Stack
              alignItems={{ xs: "stretch", md: "flex-end" }}
              direction={{ xs: "column", sm: "row", md: "column" }}
              spacing={1.5}
            >
              <Button component={RouterLink} to="/Flight" variant="contained">
                Open Flights
              </Button>
              <Button
                component={RouterLink}
                sx={{
                  borderColor: "rgba(248,250,252,0.5)",
                  color: "#f8fafc",
                }}
                to="/Gate"
                variant="outlined"
              >
                Review Gates
              </Button>
            </Stack>
          </Stack>
        </Paper>

        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              xl: "repeat(4, minmax(0, 1fr))",
            },
            mt: 2.5,
          }}
        >
          <StatCard
            icon={<WarningAmberRoundedIcon />}
            label="Delayed Flights"
            tone="linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)"
            value={String(delayedFlights.length)}
          />
          <StatCard
            icon={<FlightTakeoffRoundedIcon />}
            label="Departed Flights"
            tone="linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)"
            value={String(departedFlights.length)}
          />
          <StatCard
            icon={<AccessTimeRoundedIcon />}
            label="Total Delay Minutes"
            tone="linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)"
            value={String(totalDelayMinutes)}
          />
          <StatCard
            icon={<ConnectingAirportsRoundedIcon />}
            label="Busiest Gate"
            tone="linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)"
            value={busiestGate ? busiestGate.code : "-"}
          />
        </Box>

        <Box
          sx={{
            display: "grid",
            gap: 2.5,
            gridTemplateColumns: { xs: "1fr", lg: "2fr 1fr" },
            mt: 2.5,
          }}
        >
          <Paper elevation={0} sx={{ borderRadius: 4, overflow: "hidden", p: 2 }}>
            <Stack
              alignItems="center"
              direction="row"
              justifyContent="space-between"
              sx={{ mb: 1.5 }}
            >
              <Typography sx={{ fontWeight: 800 }} variant="h5">
                Departures Board
              </Typography>
              <Chip
                label="Sorted by schedule"
                sx={{ backgroundColor: "#e2e8f0", fontWeight: 700 }}
              />
            </Stack>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Flight</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Destination</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Gate</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Scheduled</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Actual</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      Delay
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {flights.map((flight) => {
                    const gate = gateLookup[String(flight.gate_id)];
                    const status = statuses[String(flight.status_id)];
                    const isDelayed = flight.delay_minutes > 0;
                    return (
                      <TableRow hover key={flight.id}>
                        <TableCell>
                          <Typography sx={{ fontWeight: 700 }}>
                            {flight.flight_number}
                          </Typography>
                        </TableCell>
                        <TableCell>{flight.destination}</TableCell>
                        <TableCell>{gate?.code ?? "-"}</TableCell>
                        <TableCell>
                          <Chip
                            color={
                              flight.is_departed
                                ? "success"
                                : isDelayed
                                  ? "warning"
                                  : "default"
                            }
                            label={status?.label ?? "-"}
                            size="small"
                            sx={{ fontWeight: 700 }}
                          />
                        </TableCell>
                        <TableCell>{formatTimestamp(flight.scheduled_departure)}</TableCell>
                        <TableCell>{formatTimestamp(flight.actual_departure)}</TableCell>
                        <TableCell align="right">
                          <Typography
                            sx={{
                              color: isDelayed ? "#b45309" : "text.primary",
                              fontWeight: isDelayed ? 700 : 500,
                            }}
                          >
                            {flight.delay_minutes}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Stack spacing={2.5}>
            <Paper elevation={0} sx={{ borderRadius: 4, p: 2.5 }}>
              <Typography sx={{ fontWeight: 800, mb: 1 }} variant="h5">
                Gate Pulse
              </Typography>
              <Stack spacing={1.5}>
                {gates.map((gate) => (
                  <Paper
                    elevation={0}
                    key={gate.id}
                    sx={{
                      background: "#f8fafc",
                      border: "1px solid rgba(148, 163, 184, 0.18)",
                      borderRadius: 3,
                      p: 2,
                    }}
                  >
                    <Stack
                      alignItems="center"
                      direction="row"
                      justifyContent="space-between"
                    >
                      <Box>
                        <Typography sx={{ fontWeight: 800 }} variant="h6">
                          {gate.code}
                        </Typography>
                        <Typography color="text.secondary" variant="body2">
                          Terminal {gate.terminal}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${gate.flight_count} flights`}
                        sx={{ fontWeight: 700 }}
                      />
                    </Stack>
                    <Typography sx={{ mt: 1.5 }} variant="body2">
                      Total delay minutes:{" "}
                      <Box component="span" sx={{ fontWeight: 800 }}>
                        {gate.total_delay_minutes}
                      </Box>
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>
          </Stack>
        </Box>
      </Box>
    </Box>
  );
}
