# `frontend/src/FormSection.tsx`

See also:

- [../../../specs/contracts/frontend/ui-principles.md](../../../specs/contracts/frontend/ui-principles.md)
- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file when the run-owned UX artifacts require generated forms to expose
grouped sections.

```tsx
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type FormSectionProps = {
  title: string;
  description?: ReactNode;
  children: ReactNode;
};

export default function FormSection({
  title,
  description,
  children,
}: FormSectionProps) {
  return (
    <Stack spacing={2}>
      <Box>
        <Typography component="h2" variant="h6">
          {title}
        </Typography>
        {description ? (
          <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="body2">
            {description}
          </Typography>
        ) : null}
      </Box>
      <Divider />
      <Box>{children}</Box>
    </Stack>
  );
}
```
