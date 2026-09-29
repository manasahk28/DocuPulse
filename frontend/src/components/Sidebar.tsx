import { type ChangeEvent, type FormEvent } from "react";
import { ChevronLeft, Upload, FolderOpen, Zap, X } from "lucide-react";
import { useUpload } from "../hooks/useUpload";

interface SidebarProps {
  onUploadSuccess: (documentId: string, filename: string) => void;
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
        className={`fixed inset-y-0 left-0 z-30 flex w-64 shrink-0 flex-col overflow-hidden border-r border-[#3b2d42] bg-[#140f16] transition-transform duration-300 md:static md:z-auto md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#3b2d42] px-4 py-4">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-[#d49ab1]" />
            <span className="text-base font-bold text-[#f5ecf0]">DocuPulse</span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-[#b8a5b0] transition-colors hover:bg-[#302435] hover:text-[#f5ecf0]"
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
            className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed bg-[#1b141e]/60 px-4 py-6 transition-colors ${
              isUploading
                ? "cursor-not-allowed border-[#3b2d42] opacity-50"
                : "cursor-pointer border-[#4f3d58] hover:border-[#d49ab1] hover:bg-[#251c29]/50"
            }`}
          >
            <Upload className="h-6 w-6 text-[#b8a5b0]" />
            <span className="w-full truncate text-center text-xs text-[#f5ecf0]/90">
              {file ? file.name : "Drag & drop files here, or click to select"}
            </span>
            <span className="text-center text-[10px] text-[#87737f]">
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
                status.type === "success" ? "text-emerald-300" : "text-rose-400"
              }`}
            >
              {status.message}
            </p>
          )}

          {/* Uploaded Documents */}
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-[#87737f]">
            <FolderOpen className="h-8 w-8 text-[#9e627a]" />
            <span className="text-xs text-[#b8a5b0]">
              {uploadedFileName ?? "No documents uploaded yet"}
            </span>
          </div>
        </div>

        {/* Upload Button - bottom */}
        <div className="border-t border-[#3b2d42] p-4">
          <button
            onClick={handleSubmit as () => void}
            disabled={!file || isUploading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#9e627a] px-4 py-2.5 text-sm font-medium text-[#f5ecf0] transition-colors hover:bg-[#b2718b] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {status.type === "loading" ? "Uploading..." : "Upload Document"}
          </button>
        </div>
      </aside>
    </>
  );
}
