import type { FormEvent, ReactNode } from "react";
import { Send } from "lucide-react";
import { useChat } from "../hooks/useChat";
import { MarkdownMessage } from "./MarkdownMessage";

interface ChatProps {
  isEnabled: boolean;
  children: ReactNode;
}

export function Chat({ isEnabled, children }: ChatProps) {
  const { question, setQuestion, messages, isLoading, sendQuestion, endRef } =
    useChat(isEnabled);

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
                    ? "ml-auto max-w-[80%] bg-violet-600 text-white"
                    : "mr-auto max-w-[90%] bg-[#1a1f2e] text-gray-200"
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
              <div className="mr-auto flex items-center gap-1.5 rounded-lg bg-[#1a1f2e] px-4 py-2.5">
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
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
        className="flex shrink-0 items-center gap-3 border-t border-gray-800 px-6 py-4"
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
          className="min-w-0 flex-1 rounded-lg border border-gray-700 bg-[#1a1f2e] px-4 py-2.5 text-sm text-white outline-none transition-colors placeholder:text-gray-500 focus:border-violet-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!isEnabled || isLoading || !question.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-violet-600 text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
