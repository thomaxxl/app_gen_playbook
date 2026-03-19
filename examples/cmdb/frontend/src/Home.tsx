import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import DnsRoundedIcon from "@mui/icons-material/DnsRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import ShieldRoundedIcon from "@mui/icons-material/ShieldRounded";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export default function Home() {
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
            icon={<DashboardRoundedIcon />}
            label="CMDB admin home"
            sx={{
              alignSelf: "flex-start",
              backgroundColor: "rgba(255,255,255,0.78)",
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
          <Typography maxWidth={880} variant="body1">
            This admin app manages business services, configuration items, and
            operational status definitions for a lightweight CMDB workflow. Use
            the generated CRUD resources in the sidebar or open the landing page
            for the current posture snapshot.
          </Typography>
        </Stack>

        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <Button
            component={RouterLink}
            size="large"
            to="/Service"
            variant="contained"
          >
            Open Services
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            size="large"
            to="/Landing"
            variant="outlined"
          >
            Open Landing
          </Button>
        </Stack>

        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
          <Card elevation={0} sx={{ borderRadius: 4, flex: 1 }}>
            <CardContent>
              <Stack spacing={1.5}>
                <HubRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Services
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Track service ownership and the rule-driven rollups for item
                  count, operational coverage, and aggregate risk.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
          <Card elevation={0} sx={{ borderRadius: 4, flex: 1 }}>
            <CardContent>
              <Stack spacing={1.5}>
                <DnsRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Configuration Items
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Maintain hosts, classes, environments, verification timestamps,
                  and per-item risk scores across the estate.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
          <Card elevation={0} sx={{ borderRadius: 4, flex: 1 }}>
            <CardContent>
              <Stack spacing={1.5}>
                <ShieldRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Operational Statuses
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Adjust the reference states that drive copied operational
                  fields on every configuration item.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Stack>
    </Box>
  );
}
