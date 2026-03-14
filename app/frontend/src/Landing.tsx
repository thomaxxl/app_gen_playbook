import CollectionsRoundedIcon from "@mui/icons-material/CollectionsRounded";
import FolderSharedRoundedIcon from "@mui/icons-material/FolderSharedRounded";
import ImageRoundedIcon from "@mui/icons-material/ImageRounded";
import PublicRoundedIcon from "@mui/icons-material/PublicRounded";
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

type ImageAssetRecord = {
  id: string;
  file_size_mb: number;
  filename: string;
  gallery_id: string | number | null;
  is_public: boolean;
  preview_url: string;
  published_at: string | null;
  share_status_code: string;
  status_id: string | number | null;
  title: string;
  uploaded_at: string;
};

type GalleryRecord = {
  code: string;
  id: string;
  image_count: number;
  name: string;
  owner_name: string;
  public_image_count: number;
  total_size_mb: number;
};

type ShareStatusRecord = {
  code: string;
  id: string;
  is_public: boolean;
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

  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatSize(value: number): string {
  return `${value.toFixed(1)} MB`;
}

function swatchFor(value: string): string {
  const seed = Array.from(value).reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const hue = seed % 360;
  return `linear-gradient(135deg, hsl(${hue} 72% 68%) 0%, hsl(${(hue + 52) % 360} 78% 55%) 100%)`;
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
  const [images, setImages] = useState<ImageAssetRecord[]>([]);
  const [galleries, setGalleries] = useState<GalleryRecord[]>([]);
  const [statuses, setStatuses] = useState<Record<string, ShareStatusRecord>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([
      dataProvider.getList<ImageAssetRecord>("ImageAsset", {
        pagination: { page: 1, perPage: 50 },
        sort: { field: "uploaded_at", order: "DESC" },
        filter: {},
      }),
      dataProvider.getList<GalleryRecord>("Gallery", {
        pagination: { page: 1, perPage: 20 },
        sort: { field: "total_size_mb", order: "DESC" },
        filter: {},
      }),
    ])
      .then(async ([imageResult, galleryResult]) => {
        const statusIds = Array.from(
          new Set(
            imageResult.data
              .map((row) => row.status_id)
              .filter((value): value is string | number => value != null),
          ),
        );
        const statusResult = statusIds.length
          ? await dataProvider.getMany<ShareStatusRecord>("ShareStatus", {
              ids: statusIds.map(String),
            })
          : { data: [] as ShareStatusRecord[] };

        if (!mounted) {
          return;
        }

        setImages(imageResult.data);
        setGalleries(galleryResult.data);
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
            "radial-gradient(circle at top left, #fff1d6 0%, #ffd7ba 24%, #d9f0ff 58%, #f6f7f2 100%)",
          minHeight: "100vh",
          p: 4,
        }}
      >
        <CircularProgress />
        <Typography variant="h6">Loading the Cimage control room...</Typography>
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "radial-gradient(circle at top left, #fff1d6 0%, #ffd7ba 24%, #d9f0ff 58%, #f6f7f2 100%)",
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
          Failed to load Cimage sharing and management data.
        </Typography>
        <Paper sx={{ p: 2 }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </Paper>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/ImageAsset" variant="contained">
            Open Images
          </Button>
          <Button component={RouterLink} to="/Gallery" variant="outlined">
            Open Galleries
          </Button>
        </Stack>
      </Stack>
    );
  }

  if (images.length === 0) {
    return (
      <Stack
        spacing={2}
        sx={{
          background:
            "radial-gradient(circle at top left, #fff1d6 0%, #ffd7ba 24%, #d9f0ff 58%, #f6f7f2 100%)",
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
          Cimage Control Room
        </Typography>
        <Typography color="text.secondary">
          No image assets are available yet.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button component={RouterLink} to="/ImageAsset" variant="contained">
            Create Image
          </Button>
          <Button component={RouterLink} to="/Gallery" variant="outlined">
            Review Galleries
          </Button>
        </Stack>
      </Stack>
    );
  }

  const publicImages = images.filter((image) => image.is_public);
  const totalStorageMb = galleries.reduce(
    (sum, gallery) => sum + (gallery.total_size_mb || 0),
    0,
  );
  const leadGallery = [...galleries].sort((left, right) => {
    if (right.public_image_count !== left.public_image_count) {
      return right.public_image_count - left.public_image_count;
    }
    if (right.image_count !== left.image_count) {
      return right.image_count - left.image_count;
    }
    return right.total_size_mb - left.total_size_mb;
  })[0];
  const galleryLookup = Object.fromEntries(
    galleries.map((gallery) => [String(gallery.id), gallery]),
  );
  const recentUploads = [...images].sort((left, right) => {
    return Date.parse(right.uploaded_at) - Date.parse(left.uploaded_at);
  });

  return (
    <Box
      sx={{
        background:
          "radial-gradient(circle at top left, #fff1d6 0%, #ffd7ba 24%, #d9f0ff 58%, #f6f7f2 100%)",
        minHeight: "100vh",
        p: { xs: 2, md: 4 },
      }}
    >
      <Stack spacing={3} sx={{ margin: "0 auto", maxWidth: 1380 }}>
        <Paper
          elevation={0}
          sx={{
            background:
              "linear-gradient(135deg, rgba(18, 28, 45, 0.96) 0%, rgba(28, 63, 94, 0.92) 52%, rgba(202, 86, 52, 0.84) 100%)",
            borderRadius: 6,
            color: "#f8fafc",
            overflow: "hidden",
            p: { xs: 3, md: 4.5 },
            position: "relative",
          }}
        >
          <Box
            sx={{
              background:
                "radial-gradient(circle, rgba(255,255,255,0.24) 0%, rgba(255,255,255,0) 68%)",
              height: 260,
              pointerEvents: "none",
              position: "absolute",
              right: -70,
              top: -90,
              width: 260,
            }}
          />
          <Stack spacing={3}>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              spacing={3}
            >
              <Stack spacing={1.5} sx={{ maxWidth: 760 }}>
                <Typography
                  sx={{
                    color: "rgba(248, 250, 252, 0.72)",
                    fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace',
                    letterSpacing: "0.28em",
                  }}
                  variant="overline"
                >
                  CIMAGE CONTROL ROOM
                </Typography>
                <Typography
                  sx={{
                    fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
                    fontSize: { xs: "2.5rem", md: "4rem" },
                    fontWeight: 700,
                    lineHeight: 1.02,
                  }}
                >
                  Share, stage, and track every image library.
                </Typography>
                <Typography sx={{ color: "rgba(248, 250, 252, 0.78)", maxWidth: 640 }}>
                  A live admin surface for galleries, release states, and storage
                  rollups across the Cimage media catalog.
                </Typography>
              </Stack>
              <Stack
                alignItems={{ xs: "stretch", md: "flex-end" }}
                justifyContent="space-between"
                spacing={2}
              >
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                  <Button
                    component={RouterLink}
                    sx={{ borderRadius: 999, px: 2.5 }}
                    to="/ImageAsset"
                    variant="contained"
                  >
                    Open Images
                  </Button>
                  <Button
                    color="inherit"
                    component={RouterLink}
                    sx={{
                      borderColor: "rgba(248, 250, 252, 0.36)",
                      borderRadius: 999,
                      px: 2.5,
                    }}
                    to="/Gallery"
                    variant="outlined"
                  >
                    Manage Galleries
                  </Button>
                </Stack>
                <Chip
                  label={`${leadGallery?.code ?? "-"} lead gallery`}
                  sx={{
                    alignSelf: { xs: "flex-start", md: "flex-end" },
                    background: "rgba(248, 250, 252, 0.16)",
                    color: "#f8fafc",
                    fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace',
                  }}
                />
              </Stack>
            </Stack>

            <Stack direction={{ xs: "column", sm: "row" }} flexWrap="wrap" gap={1.2}>
              <Chip
                label={`${images.length} image assets`}
                sx={{ background: "rgba(248, 250, 252, 0.12)", color: "#f8fafc" }}
              />
              <Chip
                label={`${publicImages.length} public shares`}
                sx={{ background: "rgba(248, 250, 252, 0.12)", color: "#f8fafc" }}
              />
              <Chip
                label={`${galleries.length} galleries`}
                sx={{ background: "rgba(248, 250, 252, 0.12)", color: "#f8fafc" }}
              />
            </Stack>
          </Stack>
        </Paper>

        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: {
              xs: "1fr",
              md: "repeat(2, minmax(0, 1fr))",
              xl: "repeat(4, minmax(0, 1fr))",
            },
          }}
        >
          <StatCard
            icon={<ImageRoundedIcon />}
            label="Image Assets"
            tone="linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%)"
            value={String(images.length)}
          />
          <StatCard
            icon={<PublicRoundedIcon />}
            label="Public Shares"
            tone="linear-gradient(180deg, #ecfeff 0%, #cffafe 100%)"
            value={String(publicImages.length)}
          />
          <StatCard
            icon={<CollectionsRoundedIcon />}
            label="Stored Volume"
            tone="linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%)"
            value={formatSize(totalStorageMb)}
          />
          <StatCard
            icon={<FolderSharedRoundedIcon />}
            label="Lead Gallery"
            tone="linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%)"
            value={leadGallery ? leadGallery.code : "-"}
          />
        </Box>

        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: { xs: "1fr", xl: "minmax(0, 1.55fr) minmax(360px, 0.85fr)" },
          }}
        >
          <Paper
            elevation={0}
            sx={{
              background: "rgba(255, 255, 255, 0.82)",
              border: "1px solid rgba(148, 163, 184, 0.24)",
              borderRadius: 5,
              p: { xs: 2, md: 3 },
            }}
          >
            <Stack spacing={2}>
              <Stack
                direction={{ xs: "column", sm: "row" }}
                justifyContent="space-between"
                spacing={1.5}
              >
                <Stack spacing={0.5}>
                  <Typography
                    sx={{
                      color: "#0f172a",
                      fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
                      fontWeight: 700,
                    }}
                    variant="h4"
                  >
                    Recent Uploads
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    File health, publish state, and gallery placement for the latest media.
                  </Typography>
                </Stack>
                <Button component={RouterLink} to="/ImageAsset" variant="text">
                  View all images
                </Button>
              </Stack>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Image</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Gallery</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Uploaded</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Published</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Size</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentUploads.map((image) => {
                      const gallery = galleryLookup[String(image.gallery_id)];
                      const status = statuses[String(image.status_id)];

                      return (
                        <TableRow hover key={image.id}>
                          <TableCell sx={{ minWidth: 240 }}>
                            <Stack direction="row" spacing={1.5}>
                              <Box
                                sx={{
                                  alignItems: "center",
                                  background: swatchFor(image.title),
                                  borderRadius: 3,
                                  color: "#fff",
                                  display: "flex",
                                  fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace',
                                  fontSize: "0.85rem",
                                  fontWeight: 700,
                                  height: 52,
                                  justifyContent: "center",
                                  width: 52,
                                }}
                              >
                                {image.title.slice(0, 2).toUpperCase()}
                              </Box>
                              <Stack spacing={0.25}>
                                <Typography sx={{ fontWeight: 700 }}>{image.title}</Typography>
                                <Typography color="text.secondary" variant="body2">
                                  {image.filename}
                                </Typography>
                              </Stack>
                            </Stack>
                          </TableCell>
                          <TableCell>
                            <Stack spacing={0.25}>
                              <Typography sx={{ fontWeight: 700 }}>
                                {gallery?.code ?? "-"}
                              </Typography>
                              <Typography color="text.secondary" variant="body2">
                                {gallery?.name ?? "Unknown gallery"}
                              </Typography>
                            </Stack>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={status?.label ?? image.share_status_code}
                              size="small"
                              sx={{
                                background: status?.is_public ? "#d1fae5" : "#e2e8f0",
                                color: "#0f172a",
                                fontWeight: 600,
                              }}
                            />
                          </TableCell>
                          <TableCell>{formatTimestamp(image.uploaded_at)}</TableCell>
                          <TableCell>{formatTimestamp(image.published_at)}</TableCell>
                          <TableCell>{formatSize(image.file_size_mb)}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Stack>
          </Paper>

          <Stack spacing={2}>
            <Paper
              elevation={0}
              sx={{
                background: "rgba(255, 255, 255, 0.82)",
                border: "1px solid rgba(148, 163, 184, 0.24)",
                borderRadius: 5,
                p: { xs: 2, md: 3 },
              }}
            >
              <Stack spacing={2}>
                <Stack
                  direction={{ xs: "column", sm: "row" }}
                  justifyContent="space-between"
                  spacing={1.5}
                >
                  <Stack spacing={0.5}>
                    <Typography
                      sx={{
                        color: "#0f172a",
                        fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
                        fontWeight: 700,
                      }}
                      variant="h4"
                    >
                      Gallery Pulse
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      Rollups are derived in the backend from live image assignments.
                    </Typography>
                  </Stack>
                  <Button component={RouterLink} to="/Gallery" variant="text">
                    Open galleries
                  </Button>
                </Stack>

                {galleries.map((gallery) => (
                  <Paper
                    elevation={0}
                    key={gallery.id}
                    sx={{
                      background:
                        "linear-gradient(135deg, rgba(255,247,237,0.92) 0%, rgba(239,246,255,0.92) 100%)",
                      border: "1px solid rgba(148, 163, 184, 0.2)",
                      borderRadius: 4,
                      p: 2,
                    }}
                  >
                    <Stack spacing={1.25}>
                      <Stack direction="row" justifyContent="space-between" spacing={2}>
                        <Stack spacing={0.25}>
                          <Typography
                            sx={{
                              fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace',
                              fontSize: "0.85rem",
                              letterSpacing: "0.08em",
                            }}
                          >
                            {gallery.code}
                          </Typography>
                          <Typography sx={{ fontWeight: 700 }} variant="h6">
                            {gallery.name}
                          </Typography>
                          <Typography color="text.secondary" variant="body2">
                            Owner: {gallery.owner_name}
                          </Typography>
                        </Stack>
                        <Chip label={`${gallery.image_count} images`} />
                      </Stack>
                      <Stack direction="row" flexWrap="wrap" gap={1}>
                        <Chip
                          label={`${gallery.public_image_count} public`}
                          size="small"
                          sx={{ background: "#d1fae5" }}
                        />
                        <Chip
                          label={formatSize(gallery.total_size_mb)}
                          size="small"
                          sx={{ background: "#dbeafe" }}
                        />
                      </Stack>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper
              elevation={0}
              sx={{
                background: "rgba(255, 255, 255, 0.82)",
                border: "1px solid rgba(148, 163, 184, 0.24)",
                borderRadius: 5,
                p: { xs: 2, md: 3 },
              }}
            >
              <Stack spacing={2}>
                <Stack
                  direction={{ xs: "column", sm: "row" }}
                  justifyContent="space-between"
                  spacing={1.5}
                >
                  <Stack spacing={0.5}>
                    <Typography
                      sx={{
                        color: "#0f172a",
                        fontFamily: '"Iowan Old Style", "Palatino Linotype", serif',
                        fontWeight: 700,
                      }}
                      variant="h4"
                    >
                      Share Rules
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      These statuses drive copied visibility fields and gallery public counts.
                    </Typography>
                  </Stack>
                  <Button component={RouterLink} to="/ShareStatus" variant="text">
                    Edit statuses
                  </Button>
                </Stack>

                {Object.values(statuses).map((status) => (
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    key={status.id}
                    spacing={2}
                    sx={{
                      alignItems: "center",
                      borderBottom: "1px solid rgba(226, 232, 240, 0.9)",
                      pb: 1.5,
                    }}
                  >
                    <Stack spacing={0.25}>
                      <Typography sx={{ fontWeight: 700 }}>{status.label}</Typography>
                      <Typography
                        color="text.secondary"
                        sx={{ fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace' }}
                        variant="body2"
                      >
                        {status.code}
                      </Typography>
                    </Stack>
                    <Chip
                      label={status.is_public ? "Public" : "Internal"}
                      size="small"
                      sx={{ background: status.is_public ? "#d1fae5" : "#e2e8f0" }}
                    />
                  </Stack>
                ))}
              </Stack>
            </Paper>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
}
