import AssignmentTurnedInRoundedIcon from "@mui/icons-material/AssignmentTurnedInRounded";
import EmojiEventsRoundedIcon from "@mui/icons-material/EmojiEventsRounded";
import GroupsRoundedIcon from "@mui/icons-material/GroupsRounded";
import ViewWeekRoundedIcon from "@mui/icons-material/ViewWeekRounded";
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

type PairingRecord = {
  id: string;
  black_player_id: string | number | null;
  board_number: number;
  is_reported: boolean;
  pairing_code: string;
  reported_at: string | null;
  result_summary: string | null;
  round_number: number;
  scheduled_at: string;
  status_code: string;
  status_id: string | number | null;
  tournament_id: string | number | null;
  white_player_id: string | number | null;
};

type TournamentRecord = {
  id: string;
  city: string;
  code: string;
  end_date: string | null;
  name: string;
  pairing_count: number;
  player_count: number;
  reported_pairing_count: number;
  start_date: string;
};

type PlayerRecord = {
  id: string;
  full_name: string;
  rating: number;
};

type PairingStatusRecord = {
  code: string;
  id: string;
  label: string;
};

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString([], {
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
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
  const [pairings, setPairings] = useState<PairingRecord[]>([]);
  const [players, setPlayers] = useState<Record<string, PlayerRecord>>({});
  const [statuses, setStatuses] = useState<Record<string, PairingStatusRecord>>({});
  const [tournaments, setTournaments] = useState<TournamentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([
      dataProvider.getList<PairingRecord>("Pairing", {
        pagination: { page: 1, perPage: 50 },
        sort: { field: "scheduled_at", order: "ASC" },
        filter: {},
      }),
      dataProvider.getList<TournamentRecord>("Tournament", {
        pagination: { page: 1, perPage: 20 },
        sort: { field: "start_date", order: "ASC" },
        filter: {},
      }),
    ])
      .then(async ([pairingResult, tournamentResult]) => {
        const playerIds = Array.from(
          new Set(
            pairingResult.data
              .flatMap((row) => [row.white_player_id, row.black_player_id])
              .filter((value): value is string | number => value != null),
          ),
        );
        const statusIds = Array.from(
          new Set(
            pairingResult.data
              .map((row) => row.status_id)
              .filter((value): value is string | number => value != null),
          ),
        );
        const playerResult = playerIds.length
          ? await dataProvider.getMany<PlayerRecord>("Player", {
              ids: playerIds.map(String),
            })
          : { data: [] as PlayerRecord[] };
        const statusResult = statusIds.length
          ? await dataProvider.getMany<PairingStatusRecord>("PairingStatus", {
              ids: statusIds.map(String),
            })
          : { data: [] as PairingStatusRecord[] };

        if (!mounted) {
          return;
        }

        setPairings(pairingResult.data);
        setPlayers(
          Object.fromEntries(playerResult.data.map((player) => [String(player.id), player])),
        );
        setStatuses(
          Object.fromEntries(
            statusResult.data.map((status) => [String(status.id), status]),
          ),
        );
        setTournaments(tournamentResult.data);
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
            "linear-gradient(135deg, #fbf5e6 0%, #efe4c8 42%, #d7e3ef 100%)",
          minHeight: "100vh",
          p: 4,
        }}
      >
        <CircularProgress />
        <Typography variant="h6">Loading tournament control room...</Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "linear-gradient(135deg, #fbf5e6 0%, #efe4c8 42%, #d7e3ef 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography sx={{ fontWeight: 800 }} variant="h3">
          Landing error
        </Typography>
        <Typography color="error" variant="body1">
          Failed to load chess tournament data.
        </Typography>
        <Paper sx={{ p: 2 }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </Paper>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/Pairing" variant="contained">
            Open Pairings
          </Button>
          <Button component={RouterLink} to="/Tournament" variant="outlined">
            Open Tournaments
          </Button>
        </Stack>
      </Stack>
    );
  }

  if (pairings.length === 0) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "linear-gradient(135deg, #fbf5e6 0%, #efe4c8 42%, #d7e3ef 100%)",
          minHeight: "100vh",
          p: { xs: 3, md: 5 },
        }}
      >
        <Typography sx={{ fontWeight: 800 }} variant="h3">
          Tournament Control
        </Typography>
        <Typography color="text.secondary">
          No pairings are available for the current tournament window.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/Pairing" variant="contained">
            Create Pairing
          </Button>
          <Button component={RouterLink} to="/Tournament" variant="outlined">
            Review Tournaments
          </Button>
        </Stack>
      </Stack>
    );
  }

  const reportedPairings = pairings.filter((pairing) => pairing.is_reported);
  const totalPlayers = tournaments.reduce(
    (sum, tournament) => sum + tournament.player_count,
    0,
  );
  const openBoards = pairings.length - reportedPairings.length;
  const featuredTournament = [...tournaments].sort((left, right) => {
    if (right.pairing_count !== left.pairing_count) {
      return right.pairing_count - left.pairing_count;
    }
    return right.player_count - left.player_count;
  })[0];
  const tournamentLookup = Object.fromEntries(
    tournaments.map((tournament) => [String(tournament.id), tournament]),
  );

  return (
    <Box
      sx={{
        background:
          "linear-gradient(135deg, #fbf5e6 0%, #efe4c8 42%, #d7e3ef 100%)",
        minHeight: "100vh",
        p: { xs: 2, md: 4 },
      }}
    >
      <Box sx={{ margin: "0 auto", maxWidth: 1240 }}>
        <Paper
          elevation={0}
          sx={{
            background:
              "linear-gradient(135deg, rgba(43,24,16,0.96) 0%, rgba(103,58,25,0.93) 48%, rgba(24,50,75,0.92) 100%)",
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
                sx={{
                  fontFamily: "\"Alegreya SC\", Georgia, serif",
                  fontSize: { xs: "2rem", md: "3rem" },
                  fontWeight: 900,
                  letterSpacing: "0.04em",
                }}
              >
                Tournament Control
              </Typography>
              <Typography sx={{ maxWidth: 760, opacity: 0.86 }} variant="h6">
                Track boards, rounds, and reported results across concurrent
                chess events from a single admin surface.
              </Typography>
              <Stack direction="row" flexWrap="wrap" gap={1}>
                <Chip
                  label={`${pairings.length} pairing records`}
                  sx={{
                    backgroundColor: "rgba(248,250,252,0.15)",
                    color: "#f8fafc",
                    fontWeight: 700,
                  }}
                />
                <Chip
                  label={`${tournaments.length} tournaments live`}
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
              <Button component={RouterLink} to="/Pairing" variant="contained">
                Open Pairings
              </Button>
              <Button
                component={RouterLink}
                sx={{
                  borderColor: "rgba(248,250,252,0.5)",
                  color: "#f8fafc",
                }}
                to="/Tournament"
                variant="outlined"
              >
                Review Tournaments
              </Button>
              <Button
                component={RouterLink}
                sx={{
                  borderColor: "rgba(248,250,252,0.5)",
                  color: "#f8fafc",
                }}
                to="/Player"
                variant="outlined"
              >
                Open Players
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
            icon={<EmojiEventsRoundedIcon />}
            label="Active Tournaments"
            tone="linear-gradient(135deg, #fce7c3 0%, #f7d591 100%)"
            value={String(tournaments.length)}
          />
          <StatCard
            icon={<GroupsRoundedIcon />}
            label="Players Registered"
            tone="linear-gradient(135deg, #e8f2de 0%, #cfe8bc 100%)"
            value={String(totalPlayers)}
          />
          <StatCard
            icon={<AssignmentTurnedInRoundedIcon />}
            label="Reported Pairings"
            tone="linear-gradient(135deg, #dbeafe 0%, #bfd8ff 100%)"
            value={String(reportedPairings.length)}
          />
          <StatCard
            icon={<ViewWeekRoundedIcon />}
            label="Open Boards"
            tone="linear-gradient(135deg, #f7d8d8 0%, #f0bcbc 100%)"
            value={String(openBoards)}
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
                Pairings Board
              </Typography>
              <Chip
                label="Sorted by scheduled start"
                sx={{ backgroundColor: "#e2e8f0", fontWeight: 700 }}
              />
            </Stack>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Tournament</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Board</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>White</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Black</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Result</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Scheduled</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Reported</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pairings.map((pairing) => {
                    const tournament = tournamentLookup[String(pairing.tournament_id)];
                    const white = players[String(pairing.white_player_id)];
                    const black = players[String(pairing.black_player_id)];
                    const status = statuses[String(pairing.status_id)];

                    return (
                      <TableRow hover key={pairing.id}>
                        <TableCell>
                          <Typography sx={{ fontWeight: 700 }}>
                            {tournament?.code ?? "-"}
                          </Typography>
                          <Typography color="text.secondary" variant="body2">
                            {pairing.pairing_code}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          R{pairing.round_number} / B{pairing.board_number}
                        </TableCell>
                        <TableCell>{white?.full_name ?? "-"}</TableCell>
                        <TableCell>{black?.full_name ?? "-"}</TableCell>
                        <TableCell>{pairing.result_summary ?? "-"}</TableCell>
                        <TableCell>
                          <Chip
                            color={
                              pairing.is_reported
                                ? "success"
                                : pairing.status_code === "in_progress"
                                  ? "warning"
                                  : "default"
                            }
                            label={status?.label ?? pairing.status_code}
                            size="small"
                            sx={{ fontWeight: 700 }}
                          />
                        </TableCell>
                        <TableCell>{formatDateTime(pairing.scheduled_at)}</TableCell>
                        <TableCell>{formatDateTime(pairing.reported_at)}</TableCell>
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
                Tournament Pulse
              </Typography>
              <Stack spacing={1.5}>
                {tournaments.map((tournament) => (
                  <Paper
                    elevation={0}
                    key={tournament.id}
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
                          {tournament.name}
                        </Typography>
                        <Typography color="text.secondary" variant="body2">
                          {tournament.code} • {tournament.city}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${tournament.player_count} players`}
                        sx={{ fontWeight: 700 }}
                      />
                    </Stack>
                    <Typography sx={{ mt: 1.5 }} variant="body2">
                      Pairings reported:{" "}
                      <Box component="span" sx={{ fontWeight: 800 }}>
                        {tournament.reported_pairing_count} / {tournament.pairing_count}
                      </Box>
                    </Typography>
                    <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="body2">
                      Starts {formatDateTime(tournament.start_date)}
                    </Typography>
                  </Paper>
                ))}
                {featuredTournament ? (
                  <Paper
                    elevation={0}
                    sx={{
                      background:
                        "linear-gradient(135deg, rgba(103,58,25,0.08) 0%, rgba(24,50,75,0.1) 100%)",
                      borderRadius: 3,
                      p: 2,
                    }}
                  >
                    <Typography sx={{ fontWeight: 800 }} variant="h6">
                      Featured Room
                    </Typography>
                    <Typography sx={{ mt: 0.75 }} variant="body2">
                      {featuredTournament.name} is the busiest event right now with{" "}
                      <Box component="span" sx={{ fontWeight: 800 }}>
                        {featuredTournament.pairing_count}
                      </Box>{" "}
                      boards tracked.
                    </Typography>
                  </Paper>
                ) : null}
              </Stack>
            </Paper>
          </Stack>
        </Box>
      </Box>
    </Box>
  );
}
