import { BookOpen, Upload, MessageSquare, ShieldCheck } from "lucide-react";

const features = [
  {
    icon: BookOpen,
    title: "1. Browse Documents",
    description: "View and manage your document collection",
    color: "text-[#e2b6c7]",
  },
  {
    icon: Upload,
    title: "2. Upload Files",
    description: "Upload PDFs, TXT, or DOCX files",
    color: "text-[#d49ab1]",
  },
  {
    icon: MessageSquare,
    title: "3. Ask Questions",
    description: "Get answers from your documents",
    color: "text-[#c4839d]",
  },
];

export function WelcomeContent() {
  return (
    <div className="mx-auto w-full max-w-2xl rounded-xl border border-[#3b2d42] bg-[#251c29] p-5 shadow-lg shadow-black/20 sm:p-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <ShieldCheck className="h-10 w-10 text-[#d49ab1]" />
        <h2 className="text-lg font-bold text-[#f5ecf0]">Welcome to DocuPulse</h2>
        <p className="text-sm text-[#b8a5b0]">
          Ask questions about your documents and get accurate answers powered by
          AI.
        </p>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:mt-8 sm:grid-cols-3 sm:gap-4">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="flex flex-col items-center gap-2 rounded-lg border border-[#4f3d58]/60 bg-[#302435] p-4 text-center transition-colors hover:border-[#9e627a] sm:p-5"
          >
            <feature.icon className={`h-6 w-6 ${feature.color}`} />
            <h3 className="text-sm font-semibold text-[#f5ecf0]">
              {feature.title}
            </h3>
            <p className="text-xs text-[#b8a5b0]">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
