import type { FormEvent } from "react";
import { useUpload } from "../hooks/useUpload";

interface UploadProps {
  onUploadSuccess?: () => void;
}

export function Upload({ onUploadSuccess }: UploadProps) {
  const { file, status, handleFileChange, handleUpload } = useUpload(onUploadSuccess);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    handleUpload();
  }

  return (
    <section className="rounded-xl border border-[#3b2d42] bg-[#251c29] p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-[#f5ecf0]">
        Upload Document
      </h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-[#4f3d58] p-8 transition-colors hover:border-[#d49ab1]">
          <svg
            className="mb-2 h-8 w-8 text-[#b8a5b0]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <span className="text-sm text-[#b8a5b0]">
            {file ? file.name : "Click to select a PDF or text file"}
          </span>
          <input
            type="file"
            accept=".pdf,.txt,.text"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        <button
          type="submit"
          disabled={!file || status.type === "loading"}
          className="rounded-lg bg-[#9e627a] px-4 py-2.5 text-sm font-medium text-[#f5ecf0] transition-colors hover:bg-[#b2718b] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {status.type === "loading" ? "Uploading..." : "Upload"}
        </button>
      </form>

      {status.type !== "idle" && status.type !== "loading" && (
        <p
          className={`mt-3 text-sm ${
            status.type === "success"
              ? "text-emerald-300"
              : "text-rose-400"
          }`}
        >
          {status.message}
        </p>
      )}
    </section>
  );
}
