# `frontend/src/shims/fs-promises.ts`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

This is the only canonical shim location.

```ts
export async function readFile(): Promise<string> {
  throw new Error("fs/promises is not available in the browser runtime");
}
```
