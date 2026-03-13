# `frontend/src/main.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```
