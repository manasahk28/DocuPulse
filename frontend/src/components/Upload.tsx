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
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
        Upload Document
      </h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-8 transition-colors hover:border-violet-400 dark:border-gray-600 dark:hover:border-violet-500">
          <svg
            className="mb-2 h-8 w-8 text-gray-400"
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
          <span className="text-sm text-gray-500 dark:text-gray-400">
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
          className="rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {status.type === "loading" ? "Uploading..." : "Upload"}
        </button>
      </form>

      {status.type !== "idle" && status.type !== "loading" && (
        <p
          className={`mt-3 text-sm ${
            status.type === "success"
              ? "text-green-600 dark:text-green-400"
              : "text-red-600 dark:text-red-400"
          }`}
        >
          {status.message}
        </p>
      )}
    </section>
  );
}
