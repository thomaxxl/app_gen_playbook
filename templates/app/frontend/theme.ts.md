# `frontend/src/theme.ts`

See also:

- [../../../specs/contracts/frontend/theme-and-layout.md](../../../specs/contracts/frontend/theme-and-layout.md)

Use this file for the shared starter MUI theme.

```tsx
import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  shape: {
    borderRadius: 12,
  },
  palette: {
    primary: {
      main: "#135089",
    },
    background: {
      default: "#f5f7fb",
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          border: "1px solid rgba(15, 23, 42, 0.08)",
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
    },
  },
});
```
