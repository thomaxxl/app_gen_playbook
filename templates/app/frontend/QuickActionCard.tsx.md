# `frontend/src/QuickActionCard.tsx`

See also:

- [../../../specs/contracts/frontend/home-and-entry.md](../../../specs/contracts/frontend/home-and-entry.md)
- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for short entry-page action surfaces that clarify what the user
can do next.

```tsx
import Card from "@mui/material/Card";
import CardActions from "@mui/material/CardActions";
import CardContent from "@mui/material/CardContent";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { Link as RouterLink } from "react-router-dom";

import AppIcon from "./AppIcon";

type QuickActionCardProps = {
  title: string;
  description: ReactNode;
  to: string;
  actionLabel: string;
};

export default function QuickActionCard({
  title,
  description,
  to,
  actionLabel,
}: QuickActionCardProps) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography component="h3" variant="subtitle1">
            {title}
          </Typography>
          <Typography color="text.secondary" variant="body2">
            {description}
          </Typography>
        </Stack>
      </CardContent>
      <CardActions sx={{ pt: 0 }}>
        <Link
          component={RouterLink}
          sx={{ display: "inline-flex", gap: 0.75, alignItems: "center" }}
          to={to}
          underline="hover"
        >
          {actionLabel}
          <AppIcon fontSize="inherit" name="arrow-forward" />
        </Link>
      </CardActions>
    </Card>
  );
}
```
