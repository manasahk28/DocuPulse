import { useEffect, useRef, useState } from "react";
import { queryDocument } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function useChat(isEnabled: boolean, documentId?: string | null) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  // Clear previous conversation when a new document is uploaded
  useEffect(() => {
    setMessages([]);
    setQuestion("");
  }, [documentId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  async function sendQuestion() {
    if (!isEnabled || isLoading) {
      return;
    }

    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const historyPayload = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const result = await queryDocument(trimmed, historyPayload, documentId);

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.answer,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          error instanceof Error
            ? `Error: ${error.message}`
            : "Something went wrong.",
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return { question, setQuestion, messages, isLoading, sendQuestion, endRef };
}
