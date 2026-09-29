import { useState } from "react";
import { Sidebar } from "../components/Sidebar";
import { Chat } from "../components/Chat";
import { WelcomeContent } from "../components/WelcomeContent";
import { ShieldCheck, Menu } from "lucide-react";

export function Home() {
  const [hasUploadedDocument, setHasUploadedDocument] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function handleUploadSuccess() {
    setHasUploadedDocument(true);
    setUploadedFileName("Document uploaded");
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#111827]">
      {/* Sidebar */}
      <Sidebar
        onUploadSuccess={handleUploadSuccess}
        uploadedFileName={uploadedFileName}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex shrink-0 items-center gap-3 border-b border-gray-800 px-4 py-4 md:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className={`rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white ${sidebarOpen ? "md:hidden" : ""}`}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1a1f2e]">
            <ShieldCheck className="h-5 w-5 text-gray-400" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">DocuMind</h1>
            <p className="text-xs text-gray-400">
              Ask questions about your documents
            </p>
          </div>
        </header>

        {/* Center Content / Conversation */}
        <Chat isEnabled={hasUploadedDocument}>
          <WelcomeContent />
        </Chat>
      </main>
    </div>
  );
}
