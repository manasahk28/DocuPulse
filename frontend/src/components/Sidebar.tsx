import { type ChangeEvent, type FormEvent } from "react";
import { ChevronLeft, Upload, FolderOpen, Zap, X } from "lucide-react";
import { useUpload } from "../hooks/useUpload";

interface SidebarProps {
  onUploadSuccess: () => void;
  uploadedFileName: string | null;
  open: boolean;
  onClose: () => void;
}

export function Sidebar({
  onUploadSuccess,
  uploadedFileName,
  open,
  onClose,
}: SidebarProps) {
  const { file, status, handleFileChange, handleUpload } =
    useUpload(onUploadSuccess);

  const isUploading = status.type === "loading";

  function handleDrop(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (isUploading) return;
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) {
      const fakeEvent = {
        target: { files: [droppedFile] },
      } as unknown as ChangeEvent<HTMLInputElement>;
      handleFileChange(fakeEvent);
    }
  }

  function handleDragOver(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    handleUpload();
  }

  return (
    <>
      {/* Backdrop overlay — mobile only */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 shrink-0 flex-col overflow-hidden border-r border-gray-800 bg-[#0f1219] transition-transform duration-300 md:static md:z-auto md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-800 px-4 py-4">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-violet-400" />
            <span className="text-base font-bold text-white">DocuMind</span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            <X className="h-4 w-4 md:hidden" />
            <ChevronLeft className="hidden h-4 w-4 md:block" />
          </button>
        </div>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
          {/* Drop Zone */}
          <label
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-6 transition-colors ${
              isUploading
                ? "cursor-not-allowed border-gray-700 opacity-50"
                : "cursor-pointer border-gray-600 hover:border-violet-500"
            }`}
          >
            <Upload className="h-6 w-6 text-gray-500" />
            <span className="w-full truncate text-center text-xs text-gray-400">
              {file ? file.name : "Drag & drop files here, or click to select"}
            </span>
            <span className="text-center text-[10px] text-gray-500">
              Supported: PDF, DOCX, TXT (max 10MB)
            </span>
            <input
              type="file"
              accept=".pdf,.txt,.text,.docx"
              onChange={handleFileChange}
              disabled={isUploading}
              className="hidden"
            />
          </label>

          {/* Status message */}
          {status.type !== "idle" && status.type !== "loading" && (
            <p
              className={`wrap-break-word text-xs ${
                status.type === "success" ? "text-green-400" : "text-red-400"
              }`}
            >
              {status.message}
            </p>
          )}

          {/* Uploaded Documents */}
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-gray-500">
            <FolderOpen className="h-8 w-8" />
            <span className="text-xs">
              {uploadedFileName ?? "No documents uploaded yet"}
            </span>
          </div>
        </div>

        {/* Upload Button - bottom */}
        <div className="border-t border-gray-800 p-4">
          <button
            onClick={handleSubmit as () => void}
            disabled={!file || isUploading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {status.type === "loading" ? "Uploading..." : "Upload Document"}
          </button>
        </div>
      </aside>
    </>
  );
}
