# `frontend/tsconfig.node.json`

See also:

- [../../../specs/contracts/frontend/scaffold.md](../../../specs/contracts/frontend/scaffold.md)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "skipLibCheck": true,
    "composite": true,
    "allowSyntheticDefaultImports": true,
    "types": ["node"]
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```
