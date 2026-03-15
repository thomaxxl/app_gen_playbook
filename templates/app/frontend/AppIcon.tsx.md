# `frontend/src/AppIcon.tsx`

See also:

- [../../../specs/contracts/frontend/ui-principles.md](../../../specs/contracts/frontend/ui-principles.md)
- [../../../runs/current/artifacts/ux/iconography.md](../../../runs/current/artifacts/ux/iconography.md)

Use this file as the stable app-facing icon wrapper.

The starter implementation stays lightweight and uses MUI icons by default.
If the run enables `font-awesome-icons`, adapt this wrapper instead of adding
direct icon-family imports throughout the page templates.

```tsx
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import HomeIcon from "@mui/icons-material/Home";
import LaunchIcon from "@mui/icons-material/Launch";
import type { SvgIconProps } from "@mui/material/SvgIcon";
import type { ComponentType } from "react";

type AppIconName =
  | "arrow-back"
  | "arrow-forward"
  | "home"
  | "launch";

type AppIconProps = SvgIconProps & {
  name: AppIconName;
};

const ICONS: Record<AppIconName, ComponentType<SvgIconProps>> = {
  "arrow-back": ArrowBackIcon,
  "arrow-forward": ArrowForwardIcon,
  home: HomeIcon,
  launch: LaunchIcon,
};

export default function AppIcon({ name, ...props }: AppIconProps) {
  const IconComponent = ICONS[name];
  return <IconComponent {...props} />;
}
```

Notes:

- The core template keeps the default implementation MUI-backed so Font
  Awesome stays optional.
- When `font-awesome-icons` is enabled, replace the wrapper internals and the
  supported `name` mapping according to `iconography.md` instead of scattering
  direct Font Awesome imports across page templates.
