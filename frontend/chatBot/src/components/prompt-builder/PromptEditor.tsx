"use client";

import { useState } from "react";

interface Props {
  fileContent: string;
  fileName: string;
  extractorId: string;
  repoId: string;
  contextData: any;
  onContextGenerated: (data: any) => void;
}

export default function PromptEditor({
  fileContent,
  fileName,
  extractorId,
  repoId,
  contextData,
  onContextGenerated,
}: Props) {
  const [instruction, setInstruction] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [contextLoading, setContextLoading] = useState(false);
  const [promptLoading, setPromptLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  /* =====================================================
     🧠 EMPTY STATE — NO FILE SELECTED
  ====================================================== */
  if (!fileName || !fileContent) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1E1E1E] p-6">
        <div className="text-center max-w-md">
          <div className="text-lg text-gray-300 mb-3">
            No file selected
          </div>
          <div className="text-sm text-gray-500 leading-relaxed">
            Click on any file from the project tree to view its code,
            analyze impact, and generate a context-aware prompt.
          </div>
        </div>
      </div>
    );
  }

  async function buildPrompt() {
    if (!instruction) return;

    setGeneratedPrompt("");

    try {
      let activeContext = contextData;

      if (!activeContext) {
        setContextLoading(true);

        const contextRes = await fetch(
          `http://localhost:8000/prompt-builder/${extractorId}/repos/${repoId}/context`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              file_path: fileName,
              user_instruction: instruction,
              max_depth: 2,
              max_files: 10,
            }),
          }
        );

        if (!contextRes.ok) throw new Error("Context build failed");

        activeContext = await contextRes.json();
        onContextGenerated(activeContext);

        setContextLoading(false);
      }

      setPromptLoading(true);

      const promptRes = await fetch(
        `http://localhost:8000/prompt-builder/${extractorId}/repos/${repoId}/generate-prompt`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_instruction: instruction,
            architecture_payload: {
              classification: activeContext.classification,
              file_graph: activeContext.file_graph,
              architecture_summary: activeContext.architecture_summary,
              files: activeContext.structured_context,
            },
          }),
        }
      );

      if (!promptRes.ok) throw new Error("Prompt generation failed");

      const promptData = await promptRes.json();
      setGeneratedPrompt(promptData.llm_refined_prompt ?? "");
      setPromptLoading(false);
    } catch (err) {
      console.error("Prompt build failed:", err);
      setContextLoading(false);
      setPromptLoading(false);
    }
  }

  async function copyToClipboard() {
    if (!generatedPrompt) return;

    try {
      await navigator.clipboard.writeText(generatedPrompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  }

  const isLoading = contextLoading || promptLoading;

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-[#1E1E1E] p-6 gap-6">
      {/* ================= Instruction ================= */}
      <div className="shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-400">
            What do you want to do?
          </div>

          <button
            onClick={buildPrompt}
            disabled={isLoading}
            className="text-xs bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-md text-white transition disabled:opacity-40"
          >
            {contextLoading
              ? "Analyzing Architecture..."
              : promptLoading
              ? "Generating Prompt..."
              : "Generate Full Context Prompt"}
          </button>
        </div>

        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="Example: Refactor initialization logic..."
          className="w-full h-32 bg-[#111827] text-gray-200 p-3 rounded-lg border border-[#1F2937] outline-none resize-none"
        />
      </div>

      {/* ================= Prompt Preview ================= */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="flex items-center justify-between mb-2 shrink-0">
          <div className="text-sm text-gray-400">
            Generated Context aware Prompt
          </div>

          <button
            onClick={copyToClipboard}
            disabled={!generatedPrompt}
            className="text-xs bg-[#2A2D2E] hover:bg-[#3A3D3E] px-3 py-1 rounded-md text-gray-200 transition disabled:opacity-40"
          >
            {copied ? "Prompt Copied ✓" : "Copy Prompt"}
          </button>
        </div>

        <textarea
          value={generatedPrompt}
          onChange={(e) => setGeneratedPrompt(e.target.value)}
          className="flex-1 min-h-0 bg-[#111827] text-gray-300 p-4 rounded-lg border border-[#1F2937] overflow-y-auto whitespace-pre-wrap text-sm resize-none outline-none"
        />
      </div>
    </div>
  );
}