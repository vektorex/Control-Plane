import "@/styles/globals.css";
import { siteConfig } from "@/config/site";

export const metadata = {
  title: {
    default: `${siteConfig.name} — ${siteConfig.tagline}`,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [
    "AI Work Layer",
    "LLM Orchestration",
    "Model Routing",
    "RAG",
    "FastAPI",
    "Next.js",
    "AI Agents",
  ],
  authors: [{ name: "Rayulu Mukku" }],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="bg-[#07090e] text-slate-100 min-h-screen antialiased flex flex-col">
        {children}
      </body>
    </html>
  );
}
