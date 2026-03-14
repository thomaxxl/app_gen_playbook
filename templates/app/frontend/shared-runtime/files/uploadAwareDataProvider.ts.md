# `frontend/src/shared-runtime/files/uploadAwareDataProvider.ts`

See also:

- [../../../../../specs/contracts/files/uploads-and-frontend-integration.md](../../../../../specs/contracts/files/uploads-and-frontend-integration.md)

```ts
import type { DataProvider } from "react-admin";

import type { RawAdminYaml } from "../admin/resourceMetadata";
import { containsRawFile, replaceField } from "./fileFieldHelpers";
import { isNewFileValue } from "./fileValueAdapters";

type UploadFieldMap = Record<
  string,
  Record<
    string,
    {
      targetField: string;
      purpose?: string;
    }
  >
>;

export function buildUploadFieldMap(rawYaml: RawAdminYaml): UploadFieldMap {
  return Object.fromEntries(
    Object.entries(rawYaml.resources ?? {})
      .map(([resourceName, resource]) => {
        const fieldEntries = Object.entries(resource.attributes ?? {})
          .filter(([, attribute]) => attribute.type === "file" || attribute.type === "image")
          .map(([fieldName, attribute]) => {
            if (!attribute.upload_target) {
              throw new Error(
                `Upload field '${resourceName}.${fieldName}' is missing upload_target.`,
              );
            }

            return [
              fieldName,
              {
                targetField: attribute.upload_target,
                purpose: attribute.purpose,
              },
            ] as const;
          });

        return [resourceName, Object.fromEntries(fieldEntries)] as const;
      })
      .filter(([, fields]) => Object.keys(fields).length > 0),
  );
}

async function createPendingStoredFile(
  apiRoot: string,
  fileName: string,
  purpose?: string,
): Promise<{ id: string }> {
  const response = await fetch(`${apiRoot}/stored_files`, {
    method: "POST",
    headers: {
      Accept: "application/vnd.api+json",
      "Content-Type": "application/vnd.api+json",
    },
    body: JSON.stringify({
      data: {
        type: "stored_files",
        attributes: {
          original_filename: fileName,
          purpose,
          status: "pending",
        },
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create pending file metadata: ${response.status}`);
  }

  const payload = await response.json();
  return { id: String(payload.data.id) };
}

async function uploadStoredFileContent(
  apiRoot: string,
  fileId: string,
  rawFile: File,
  purpose?: string,
): Promise<void> {
  const form = new FormData();
  form.append("file", rawFile);
  if (purpose) {
    form.append("purpose", purpose);
  }

  const response = await fetch(`${apiRoot}/stored_files/${fileId}/content`, {
    method: "PUT",
    body: form,
  });

  if (!response.ok) {
    throw new Error(`Failed to upload file content: ${response.status}`);
  }
}

async function materializeUploads(
  resourceName: string,
  apiRoot: string,
  data: Record<string, unknown>,
  uploadFieldMap: UploadFieldMap,
): Promise<Record<string, unknown>> {
  let nextData = { ...data };
  const resourceFieldMap = uploadFieldMap[resourceName] ?? {};

  for (const [fieldName, config] of Object.entries(resourceFieldMap)) {
    const value = nextData[fieldName];
    if (!containsRawFile(value)) {
      continue;
    }

    if (!isNewFileValue(value)) {
      throw new Error(`Upload field '${fieldName}' must contain a single file value in the starter contract.`);
    }

    const pending = await createPendingStoredFile(apiRoot, value.title, config.purpose);
    await uploadStoredFileContent(apiRoot, pending.id, value.rawFile, config.purpose);

    nextData = replaceField(nextData, config.targetField, pending.id);
    delete nextData[fieldName];
  }

  return nextData;
}

export function createUploadAwareDataProvider(
  baseProvider: DataProvider,
  options: {
    apiRoot: string;
    uploadFieldMap: UploadFieldMap;
  },
): DataProvider {
  return {
    ...baseProvider,
    async create(resource, params) {
      const data = await materializeUploads(
        String(resource),
        options.apiRoot,
        params.data as Record<string, unknown>,
        options.uploadFieldMap,
      );
      return baseProvider.create(resource, { ...params, data });
    },
    async update(resource, params) {
      const data = await materializeUploads(
        String(resource),
        options.apiRoot,
        params.data as Record<string, unknown>,
        options.uploadFieldMap,
      );
      return baseProvider.update(resource, { ...params, data });
    },
  };
}
```

Notes:

- The starter helper derives upload mapping from raw `admin.yaml` so the
  upload path remains schema-driven.
- The map is per resource. Do not use one flat global field map across
  unrelated resources.
- The starter helper intentionally supports single-file fields only.
