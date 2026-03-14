# `frontend/src/shared-runtime/files/fileValueAdapters.ts`

```ts
export interface ExistingFileValue {
  id: string;
  title: string;
  src: string;
  media_type?: string;
}

export interface NewFileValue {
  title: string;
  src: string;
  rawFile: File;
}

export function isNewFileValue(value: unknown): value is NewFileValue {
  return Boolean(
    value
      && typeof value === "object"
      && "rawFile" in (value as Record<string, unknown>)
      && (value as { rawFile?: unknown }).rawFile instanceof File,
  );
}

export function isExistingFileValue(value: unknown): value is ExistingFileValue {
  return Boolean(
    value
      && typeof value === "object"
      && typeof (value as { id?: unknown }).id === "string"
      && typeof (value as { src?: unknown }).src === "string",
  );
}
```
