# `frontend/src/EmptyState.tsx`

See also:

- [../../../specs/contracts/frontend/ui-principles.md](../../../specs/contracts/frontend/ui-principles.md)

Use this file for shared no-data or no-results screens.

```tsx
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  message: ReactNode;
  action?: ReactNode;
};

export default function EmptyState({
  title,
  message,
  action,
}: EmptyStateProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={1.5}>
        <Typography component="h2" variant="h6">
          {title}
        </Typography>
        <Typography color="text.secondary" variant="body1">
          {message}
        </Typography>
        {action}
      </Stack>
    </Paper>
  );
}
```
