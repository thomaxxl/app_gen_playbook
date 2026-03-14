# `frontend/src/ErrorState.tsx`

See also:

- [../../../specs/contracts/frontend/ui-principles.md](../../../specs/contracts/frontend/ui-principles.md)
- [../../../specs/contracts/frontend/accessibility.md](../../../specs/contracts/frontend/accessibility.md)

Use this file for shared page-level error screens.

```tsx
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type ErrorStateProps = {
  title: string;
  message: ReactNode;
  details?: string;
  action?: ReactNode;
};

export default function ErrorState({
  title,
  message,
  details,
  action,
}: ErrorStateProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={1.5}>
        <Typography component="h2" variant="h6">
          {title}
        </Typography>
        <Typography color="error" variant="body1">
          {message}
        </Typography>
        {details ? (
          <Typography
            component="pre"
            sx={{ m: 0, overflowX: "auto", whiteSpace: "pre-wrap" }}
            variant="body2"
          >
            {details}
          </Typography>
        ) : null}
        {action}
      </Stack>
    </Paper>
  );
}
```
