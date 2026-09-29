import { BookOpen, Upload, MessageSquare, ShieldCheck } from "lucide-react";

const features = [
  {
    icon: BookOpen,
    title: "1. Browse Documents",
    description: "View and manage your document collection",
    color: "text-emerald-400",
  },
  {
    icon: Upload,
    title: "2. Upload Files",
    description: "Upload PDFs, TXT, or DOCX files",
    color: "text-emerald-400",
  },
  {
    icon: MessageSquare,
    title: "3. Ask Questions",
    description: "Get answers from your documents",
    color: "text-violet-400",
  },
];

export function WelcomeContent() {
  return (
    <div className="mx-auto w-full max-w-2xl rounded-xl border border-gray-700/50 bg-[#1a1f2e] p-5 sm:p-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <ShieldCheck className="h-10 w-10 text-gray-400" />
        <h2 className="text-lg font-bold text-white">Welcome to DocuMind</h2>
        <p className="text-sm text-gray-400">
          Ask questions about your documents and get accurate answers powered by
          AI.
        </p>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:mt-8 sm:grid-cols-3 sm:gap-4">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="flex flex-col items-center gap-2 rounded-lg border border-gray-700/50 bg-[#232838] p-4 text-center sm:p-5"
          >
            <feature.icon className={`h-6 w-6 ${feature.color}`} />
            <h3 className="text-sm font-semibold text-white">
              {feature.title}
            </h3>
            <p className="text-xs text-gray-400">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
