# `frontend/src/SummaryCard.tsx`

See also:

- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for compact summary surfaces on `Home` or custom pages.

```tsx
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type SummaryCardProps = {
  title: string;
  description?: ReactNode;
  children: ReactNode;
};

export default function SummaryCard({
  title,
  description,
  children,
}: SummaryCardProps) {
  return (
    <Card sx={{ flex: 1, minWidth: 240 }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography component="h2" variant="subtitle1">
            {title}
          </Typography>
          {description ? (
            <Typography color="text.secondary" variant="body2">
              {description}
            </Typography>
          ) : null}
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}
```
