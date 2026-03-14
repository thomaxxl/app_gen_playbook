import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import FolderRoundedIcon from "@mui/icons-material/FolderRounded";
import ImageRoundedIcon from "@mui/icons-material/ImageRounded";
import PublicRoundedIcon from "@mui/icons-material/PublicRounded";
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
          "radial-gradient(circle at top left, #fff1d6 0%, #ffd7ba 24%, #d9f0ff 58%, #f6f7f2 100%)",
        minHeight: "100vh",
        p: { xs: 3, md: 5 },
      }}
    >
      <Stack spacing={3}>
        <Stack spacing={1.5}>
          <Chip
            icon={<DashboardRoundedIcon />}
            label="Cimage admin home"
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
            Cimage Sharing and Management
          </Typography>
          <Typography maxWidth={880} variant="body1">
            This admin app manages galleries, uploaded image assets, and share
            statuses for the Cimage workflow. Use the sidebar to browse the
            generated React-admin resources, or open the visual landing page for
            a richer at-a-glance summary.
          </Typography>
        </Stack>

        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <Button
            component={RouterLink}
            size="large"
            to="/Gallery"
            variant="contained"
          >
            Open Galleries
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
                <FolderRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Galleries
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Browse collections, owners, and the derived gallery metrics
                  maintained by the backend rules.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
          <Card elevation={0} sx={{ borderRadius: 4, flex: 1 }}>
            <CardContent>
              <Stack spacing={1.5}>
                <ImageRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Image Assets
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Manage uploaded files, preview metadata, and follow
                  publication state through the generated CRUD pages.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
          <Card elevation={0} sx={{ borderRadius: 4, flex: 1 }}>
            <CardContent>
              <Stack spacing={1.5}>
                <PublicRoundedIcon color="primary" />
                <Typography fontWeight={700} variant="h6">
                  Share Statuses
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Inspect the status definitions that drive copied visibility
                  fields and publication constraints.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Stack>
    </Box>
  );
}
