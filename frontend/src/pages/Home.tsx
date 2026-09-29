import { useState } from "react";
import { Sidebar } from "../components/Sidebar";
import { Chat } from "../components/Chat";
import { WelcomeContent } from "../components/WelcomeContent";
import { ShieldCheck, Menu } from "lucide-react";

export function Home() {
  const [hasUploadedDocument, setHasUploadedDocument] = useState(false);
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(
    null,
  );
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function handleUploadSuccess(documentId: string, filename: string) {
    setHasUploadedDocument(true);
    setUploadedDocumentId(documentId);
    setUploadedFileName(filename);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#1b141e]">
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
        <header className="flex shrink-0 items-center gap-3 border-b border-[#3b2d42] bg-[#1b141e]/90 px-4 py-4 backdrop-blur-sm md:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className={`rounded p-1 text-[#b8a5b0] transition-colors hover:bg-[#302435] hover:text-[#f5ecf0] ${sidebarOpen ? "md:hidden" : ""}`}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#3b2d42] bg-[#251c29]">
            <ShieldCheck className="h-5 w-5 text-[#d49ab1]" />
          </div>
          <div>
            <h1 className="text-base font-bold text-[#f5ecf0]">DocuPulse</h1>
            <p className="text-xs text-[#b8a5b0]">
              Ask questions about your documents
            </p>
          </div>
        </header>

        {/* Center Content / Conversation */}
        <Chat isEnabled={hasUploadedDocument} documentId={uploadedDocumentId}>
          <WelcomeContent />
        </Chat>
      </main>
    </div>
  );
}
