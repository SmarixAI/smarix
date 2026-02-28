"use client";

import { useState } from "react";

interface Props {
  content: string;
}

export default function CodeViewer({ content }: Props) {
  const [copied, setCopied] = useState(false);

  if (!content) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1E1E1E] text-gray-500">
        Select a file to view content
      </div>
    );
  }

  const lines = content.split("\n");

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      console.error("Copy failed");
    }
  }

  return (
    <div className="relative flex-1 overflow-auto bg-[#1E1E1E] font-mono text-sm">

      {/* Copy Button */}
      <button
        onClick={handleCopy}
        className="absolute top-4 right-4 bg-[#2A2D2E] hover:bg-[#3A3D3E] text-xs px-3 py-1 rounded-lg text-gray-300 transition"
      >
        {copied ? "Copied!" : "Copy Code"}
      </button>

      <div className="inline-block min-w-full p-4 pt-12">

        {lines.map((line, i) => (
          <div key={i} className="flex hover:bg-[#2A2D2E]">

            <span className="w-12 text-right pr-4 text-[#858585] select-none shrink-0">
              {i + 1}
            </span>

            <span className="whitespace-pre text-gray-200">
              {line}
            </span>

          </div>
        ))}

      </div>
    </div>
  );
}