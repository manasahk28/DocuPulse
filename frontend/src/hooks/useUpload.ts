import { useState, type ChangeEvent } from "react";
import { uploadDocument } from "../api/client";

interface UploadStatus {
  type: "idle" | "loading" | "success" | "error";
  message: string;
}

export function useUpload(onUploadSuccess?: () => void) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>({
    type: "idle",
    message: "",
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setStatus({ type: "idle", message: "" });
  }

  async function handleUpload() {
    if (!file) {
      setStatus({ type: "error", message: "Please select a file first." });
      return;
    }

    setStatus({ type: "loading", message: "Uploading..." });

    try {
      const result = await uploadDocument(file);
      setStatus({
        type: "success",
        message: `Uploaded \"${result.filename}\" successfully.`,
      });
      setFile(null);
      onUploadSuccess?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setStatus({ type: "error", message });
    }
  }

  return { file, status, handleFileChange, handleUpload };
}
