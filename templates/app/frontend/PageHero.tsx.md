# `frontend/src/PageHero.tsx`

See also:

- [../../../specs/contracts/frontend/home-and-entry.md](../../../specs/contracts/frontend/home-and-entry.md)
- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for the primary hero block on `Home` or an approved primary
entry page.

```tsx
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type PageHeroProps = {
  title: string;
  description: ReactNode;
  eyebrow?: string;
  actions?: ReactNode;
};

export default function PageHero({
  title,
  description,
  eyebrow,
  actions,
}: PageHeroProps) {
  return (
    <Box
      sx={{
        bgcolor: "background.paper",
        borderRadius: 3,
        p: { xs: 3, md: 4 },
      }}
    >
      <Stack
        alignItems={{ xs: "stretch", md: "flex-start" }}
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={2}
      >
        <Box sx={{ minWidth: 0 }}>
          {eyebrow ? (
            <Typography color="primary.main" sx={{ mb: 1 }} variant="overline">
              {eyebrow}
            </Typography>
          ) : null}
          <Typography component="h1" variant="h3">
            {title}
          </Typography>
          <Typography
            color="text.secondary"
            data-testid="entry-purpose"
            sx={{ mt: 1.25, maxWidth: 760 }}
            variant="body1"
          >
            {description}
          </Typography>
        </Box>

        {actions ? <Box sx={{ flexShrink: 0 }}>{actions}</Box> : null}
      </Stack>
    </Box>
  );
}
```
