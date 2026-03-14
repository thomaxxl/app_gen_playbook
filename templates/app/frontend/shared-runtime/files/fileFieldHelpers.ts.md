# `frontend/src/shared-runtime/files/fileFieldHelpers.ts`

```ts
import { isNewFileValue } from "./fileValueAdapters";

export function containsRawFile(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some(containsRawFile);
  }

  return isNewFileValue(value);
}

export function replaceField<T extends Record<string, unknown>>(
  data: T,
  fieldName: string,
  nextValue: unknown,
): T {
  return {
    ...data,
    [fieldName]: nextValue,
  };
}
```

Notes:

- The starter helper set assumes single-file fields, not multi-file arrays.
