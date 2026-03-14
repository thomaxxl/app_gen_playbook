# `frontend/src/PageHeader.tsx`

See also:

- [../../../specs/contracts/frontend/ui-principles.md](../../../specs/contracts/frontend/ui-principles.md)
- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for the shared page-header pattern.

```tsx
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { Link as RouterLink } from "react-router-dom";

type PageHeaderProps = {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  backTo?: string;
  backLabel?: string;
};

export default function PageHeader({
  title,
  description,
  actions,
  backTo,
  backLabel = "Back",
}: PageHeaderProps) {
  return (
    <Box sx={{ display: "grid", gap: 1.5, mb: 3 }}>
      {backTo ? (
        <Box>
          <Button
            component={RouterLink}
            size="small"
            startIcon={<ArrowBackIcon />}
            to={backTo}
          >
            {backLabel}
          </Button>
        </Box>
      ) : null}

      <Stack
        alignItems={{ md: "flex-start" }}
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={2}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography component="h1" variant="h4">
            {title}
          </Typography>
          {description ? (
            <Typography color="text.secondary" sx={{ mt: 0.75 }} variant="body1">
              {description}
            </Typography>
          ) : null}
        </Box>

        {actions ? <Box sx={{ flexShrink: 0 }}>{actions}</Box> : null}
      </Stack>
    </Box>
  );
}
```
