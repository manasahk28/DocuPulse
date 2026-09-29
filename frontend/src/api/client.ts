import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.PROD
    ? "https://docsystem.onrender.com"
    : "http://localhost:8000");

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

interface UploadResponse {
  message: string;
  filename: string;
  document_id: string;
  chunk_count: number;
}

interface QueryResponse {
  answer: string;
  context?: Array<{
    content: string;
    metadata: Record<string, unknown>;
    distance: number;
  }>;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
  }

  return fallback;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await api.post<UploadResponse>("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 600000,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Upload failed"));
  }
}

export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export async function queryDocument(
  question: string,
  history: ChatHistoryItem[] = [],
  documentId?: string | null,
): Promise<QueryResponse> {
  try {
    const response = await api.post<QueryResponse>("/query", {
      question,
      history,
      ...(documentId ? { document_id_filter: documentId } : {}),
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Query failed"));
  }
}
