import type { FormEvent, ReactNode } from "react";
import { Send } from "lucide-react";
import { useChat } from "../hooks/useChat";
import { MarkdownMessage } from "./MarkdownMessage";

interface ChatProps {
  isEnabled: boolean;
  documentId?: string | null;
  children: ReactNode;
}

export function Chat({ isEnabled, documentId, children }: ChatProps) {
  const { question, setQuestion, messages, isLoading, sendQuestion, endRef } =
    useChat(isEnabled, documentId);

  const hasMessages = messages.length > 0 || isLoading;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    sendQuestion();
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Show welcome content when no conversation, otherwise show messages */}
      {hasMessages ? (
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="mx-auto flex max-w-3xl flex-col gap-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                  message.role === "user"
                    ? "ml-auto max-w-[80%] bg-[#9e627a] text-[#f5ecf0]"
                    : "mr-auto max-w-[90%] border border-[#3b2d42] bg-[#251c29] text-[#f5ecf0]"
                }`}
              >
                {message.role === "assistant" ? (
                  <MarkdownMessage content={message.content} />
                ) : (
                  message.content
                )}
              </div>
            ))}

            {isLoading && (
              <div className="mr-auto flex items-center gap-1.5 rounded-lg border border-[#3b2d42] bg-[#251c29] px-4 py-2.5">
                <span className="h-2 w-2 animate-bounce rounded-full bg-[#d49ab1] [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[#d49ab1] [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[#d49ab1] [animation-delay:300ms]" />
              </div>
            )}

            <div ref={endRef} />
          </div>
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center overflow-y-auto p-6">
          {children}
        </div>
      )}

      {/* Input bar — always pinned at bottom */}
      <form
        onSubmit={handleSubmit}
        className="flex shrink-0 items-center gap-3 border-t border-[#3b2d42] px-6 py-4"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            isEnabled
              ? "Ask something about your document..."
              : "Upload documents first to ask questions"
          }
          disabled={!isEnabled || isLoading}
          className="min-w-0 flex-1 rounded-lg border border-[#4f3d58] bg-[#251c29] px-4 py-2.5 text-sm text-[#f5ecf0] outline-none transition-colors placeholder:text-[#87737f] focus:border-[#d49ab1] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!isEnabled || isLoading || !question.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#9e627a] text-[#f5ecf0] transition-colors hover:bg-[#b2718b] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
