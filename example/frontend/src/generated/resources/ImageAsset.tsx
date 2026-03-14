import { Box, Typography } from "@mui/material";
import {
  AutocompleteInput,
  BooleanField,
  Create,
  DateField,
  DateTimeInput,
  Edit,
  FileField,
  FileInput,
  ImageField,
  NumberField,
  ReferenceField,
  ReferenceInput,
  Show,
  SimpleForm,
  SimpleShowLayout,
  TextField,
  TextInput,
  required,
} from "react-admin";

import { makeSchemaDrivenPages } from "../../shared-runtime/resourceRegistry";

interface UploadedImageResponse {
  file_size_mb: number;
  filename: string;
  preview_url: string;
}

interface UploadSelection {
  rawFile?: File;
  src?: string;
  title?: string;
}

interface ImageAssetFormData {
  file_size_mb?: number;
  filename?: string;
  gallery_id?: number | string | null;
  preview_url?: string;
  published_at?: string | null;
  status_id?: number | string | null;
  title?: string;
  upload_file?: UploadSelection[] | UploadSelection | File | null;
  uploaded_at?: string;
}

const basePages = makeSchemaDrivenPages("ImageAsset");

function toNullableNumber(value: number | string | null | undefined) {
  if (value == null || value === "") {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : value;
}

function toNullableDateTime(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString();
}

export function extractRawFile(value: ImageAssetFormData["upload_file"]): File | null {
  const selected = Array.isArray(value) ? value[0] : value;
  if (selected instanceof File) {
    return selected;
  }
  if (
    selected
    && typeof selected === "object"
    && "rawFile" in selected
    && selected.rawFile instanceof File
  ) {
    return selected.rawFile;
  }
  return null;
}

export async function uploadImageFile(
  file: File,
  fetchImpl: typeof fetch = fetch,
): Promise<UploadedImageResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetchImpl("/api/uploads/images", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    let detail = `Image upload failed (${response.status})`;
    try {
      const payload = (await response.json()) as {
        detail?: string;
        errors?: Array<{ detail?: string }>;
      };
      detail = payload.detail ?? payload.errors?.[0]?.detail ?? detail;
    } catch {
      // Keep the fallback message when the response is not JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as UploadedImageResponse;
}

export async function prepareImageAssetPayload(
  data: ImageAssetFormData,
  options: {
    fetchImpl?: typeof fetch;
    previousData?: Partial<ImageAssetFormData>;
  } = {},
): Promise<Record<string, unknown>> {
  const { fetchImpl = fetch } = options;
  const nextPayload: Record<string, unknown> = {
    ...data,
    gallery_id: toNullableNumber(data.gallery_id),
    published_at: toNullableDateTime(data.published_at),
    status_id: toNullableNumber(data.status_id),
  };

  delete nextPayload.upload_file;

  const selectedFile = extractRawFile(data.upload_file);
  if (!selectedFile) {
    return nextPayload;
  }

  const uploaded = await uploadImageFile(selectedFile, fetchImpl);
  return {
    ...nextPayload,
    file_size_mb: uploaded.file_size_mb,
    filename: uploaded.filename,
    preview_url: uploaded.preview_url,
    uploaded_at: new Date().toISOString(),
  };
}

function ImagePreviewCard() {
  return (
    <Box
      sx={{
        background: "rgba(241, 245, 249, 0.68)",
        border: "1px solid rgba(148, 163, 184, 0.3)",
        borderRadius: 3,
        mb: 2,
        overflow: "hidden",
        p: 2,
      }}
    >
      <Typography sx={{ fontWeight: 700, mb: 1 }} variant="body2">
        Current Preview
      </Typography>
      <ImageField
        source="preview_url"
        sx={{
          "& img": {
            borderRadius: 2,
            maxHeight: 220,
            maxWidth: "100%",
            objectFit: "cover",
          },
        }}
        title="filename"
      />
    </Box>
  );
}

function ImageAssetFormFields({ requireUpload }: { requireUpload: boolean }) {
  return (
    <>
      <ImagePreviewCard />
      <TextInput fullWidth label="Title" source="title" validate={[required()]} />
      <ReferenceInput label="Gallery" reference="Gallery" source="gallery_id">
        <AutocompleteInput optionText="code" validate={[required()]} />
      </ReferenceInput>
      <ReferenceInput label="Share Status" reference="ShareStatus" source="status_id">
        <AutocompleteInput optionText="label" validate={[required()]} />
      </ReferenceInput>
      <DateTimeInput fullWidth label="Published At" source="published_at" />
      <FileInput
        accept={{ "image/*": [] }}
        helperText={
          requireUpload
            ? "Upload an image file to create the asset."
            : "Upload a new image file to replace the current asset."
        }
        label="Upload Image"
        multiple={false}
        source="upload_file"
        validate={requireUpload ? [required()] : undefined}
      >
        <FileField source="src" title="title" />
      </FileInput>
      <TextInput disabled fullWidth label="Stored Filename" source="filename" />
      <TextInput disabled fullWidth label="Preview URL" source="preview_url" />
      <TextInput disabled fullWidth label="Uploaded At" source="uploaded_at" />
      <TextInput disabled fullWidth label="File Size (MB)" source="file_size_mb" />
    </>
  );
}

function ImageAssetCreatePage() {
  return (
    <Create transform={(data) => prepareImageAssetPayload(data as ImageAssetFormData)}>
      <SimpleForm sanitizeEmptyValues>
        <ImageAssetFormFields requireUpload />
      </SimpleForm>
    </Create>
  );
}

function ImageAssetEditPage() {
  return (
    <Edit
      transform={(data, context) =>
        prepareImageAssetPayload(data as ImageAssetFormData, {
          previousData: context?.previousData as Partial<ImageAssetFormData> | undefined,
        })
      }
    >
      <SimpleForm sanitizeEmptyValues>
        <ImageAssetFormFields requireUpload={false} />
      </SimpleForm>
    </Edit>
  );
}

function ImageAssetShowPage() {
  return (
    <Show>
      <SimpleShowLayout>
        <ImageField
          source="preview_url"
          sx={{
            "& img": {
              borderRadius: 2,
              maxHeight: 320,
              maxWidth: "100%",
              objectFit: "cover",
            },
          }}
          title="filename"
        />
        <TextField source="title" />
        <TextField source="filename" />
        <ReferenceField label="Gallery" reference="Gallery" source="gallery_id">
          <TextField source="code" />
        </ReferenceField>
        <ReferenceField label="Share Status" reference="ShareStatus" source="status_id">
          <TextField source="label" />
        </ReferenceField>
        <DateField label="Uploaded At" source="uploaded_at" showTime />
        <DateField label="Published At" source="published_at" showTime />
        <NumberField label="File Size (MB)" source="file_size_mb" />
        <BooleanField label="Public" source="is_public" />
        <TextField label="Preview URL" source="preview_url" />
      </SimpleShowLayout>
    </Show>
  );
}

ImageAssetCreatePage.displayName = "ImageAssetCreatePage";
ImageAssetEditPage.displayName = "ImageAssetEditPage";
ImageAssetShowPage.displayName = "ImageAssetShowPage";

export const ImageAssetPages = {
  ...basePages,
  create: ImageAssetCreatePage,
  edit: ImageAssetEditPage,
  show: ImageAssetShowPage,
};
