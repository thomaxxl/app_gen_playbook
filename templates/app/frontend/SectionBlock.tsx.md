# `frontend/src/SectionBlock.tsx`

See also:

- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for reusable entry-page or dashboard sections with a heading,
optional description, and optional section-level action.

```tsx
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type SectionBlockProps = {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
};

export default function SectionBlock({
  title,
  description,
  action,
  children,
}: SectionBlockProps) {
  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Stack
        alignItems={{ xs: "stretch", md: "center" }}
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={1.5}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography component="h2" variant="h5">
            {title}
          </Typography>
          {description ? (
            <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="body2">
              {description}
            </Typography>
          ) : null}
        </Box>
        {action ? <Box sx={{ flexShrink: 0 }}>{action}</Box> : null}
      </Stack>
      {children}
    </Box>
  );
}
```
