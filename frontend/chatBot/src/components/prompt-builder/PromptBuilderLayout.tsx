"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/impact-analyzer/sidebar/Sidebar";
import CodeViewer from "@/components/impact-analyzer/main/CodeViewer";
import PromptEditor from "./PromptEditor";
import PromptRightSidebar from "./PromptRightSidebar";

const API_BASE = "http://localhost:8000";

type ViewMode = "code" | "prompt";

export default function PromptBuilderLayout() {
  const [tree, setTree] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");

  const [extractorId, setExtractorId] = useState<string>("");
  const [repoId, setRepoId] = useState<string>("");

  const [viewMode, setViewMode] = useState<ViewMode>("code");

  const [promptContext, setPromptContext] = useState<any>(null);

  /* ================= Load Project Structure ================= */

  useEffect(() => {
    if (!extractorId || !repoId) return;

    async function loadStructure() {
      try {
        const res = await fetch(
          `${API_BASE}/impact/${extractorId}/repos/${repoId}/project-structure`
        );

        if (!res.ok) throw new Error();

        const data = await res.json();
        setTree(Array.isArray(data.tree) ? data.tree : []);
      } catch {
        setTree([]);
      }
    }

    loadStructure();
  }, [extractorId, repoId]);

  /* ================= Load File Content ================= */

  useEffect(() => {
    if (!selectedFile) return;

    async function loadFileData() {
      try {
        const encodedPath = encodeURIComponent(selectedFile);

        const res = await fetch(
          `${API_BASE}/impact/${extractorId}/repos/${repoId}/file-content?path=${encodedPath}`
        );

        if (!res.ok) throw new Error();

        const data = await res.json();
        setFileContent(data.content ?? "");
      } catch {
        setFileContent("");
      }
    }

    loadFileData();
    setPromptContext(null);

  }, [selectedFile, extractorId, repoId]);

  return (
    <div className="flex h-screen bg-[#0B1220] text-gray-200">

      {/* ================= LEFT SIDEBAR ================= */}
      <Sidebar
        tree={tree}
        extractorId={extractorId}
        repoId={repoId}
        onSelectFile={setSelectedFile}
        onProjectChange={(ext, repo) => {
          setExtractorId(ext);
          setRepoId(repo);
          setSelectedFile(null);
          setPromptContext(null);
        }}
      />

      {/* ================= MAIN AREA ================= */}
      <div className="flex flex-col flex-1 min-w-0 border-l border-[#1F2937]">

        {/* ================= GLOBAL HEADER (ALWAYS FIXED) ================= */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#0F172A] border-b border-[#1F2937]">

          {/* File Info */}
          <div className="min-w-0">
            <div className="text-sm font-semibold text-white truncate">
              {selectedFile
                ? selectedFile.split("/").pop()
                : "No file selected"}
            </div>

            {selectedFile && (
              <div className="text-xs text-gray-500 truncate">
                {selectedFile}
              </div>
            )}
          </div>

          {/* Switch Buttons (Always Top Right) */}
          <div className="flex items-center bg-[#111827] border border-[#1F2937] rounded-xl p-1">
            <SegmentButton
              active={viewMode === "code"}
              onClick={() => setViewMode("code")}
              disabled={!selectedFile}
            >
              Code
            </SegmentButton>

            <SegmentButton
              active={viewMode === "prompt"}
              onClick={() => setViewMode("prompt")}
              disabled={!selectedFile}
            >
              Prompt Builder
            </SegmentButton>
          </div>
        </div>

        {/* ================= BODY ================= */}
        <div className="flex-1 min-h-0 flex">

          {/* CENTER CONTENT */}
          <div className="flex-1 min-h-0 flex">

            {/* CODE VIEW */}
            <div
              className={`flex-1 min-h-0 ${
                viewMode === "code" ? "flex" : "hidden"
              }`}
            >
              <CodeViewer
                content={fileContent}
                fileName={selectedFile ?? undefined}
              />
            </div>

            {/* PROMPT VIEW */}
            <div
              className={`flex-1 min-h-0 ${
                viewMode === "prompt" ? "flex" : "hidden"
              }`}
            >
              {selectedFile && (
                <PromptEditor
                  fileContent={fileContent}
                  fileName={selectedFile}
                  extractorId={extractorId}
                  repoId={repoId}
                  onContextGenerated={setPromptContext}
                />
              )}
            </div>
          </div>

          {/* RIGHT SIDEBAR (Now BELOW HEADER, NOT PUSHING IT) */}
          {viewMode === "prompt" && (
            <PromptRightSidebar contextData={promptContext} />
          )}

        </div>
      </div>
    </div>
  );
}

/* ================= UI ================= */

function SegmentButton({ children, active, onClick, disabled }: any) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        px-4 py-2 text-xs font-medium rounded-lg transition-all duration-200
        ${
          active
            ? "bg-blue-600 text-white"
            : "text-gray-400 hover:text-white hover:bg-[#162036]"
        }
        ${
          disabled
            ? "opacity-40 cursor-not-allowed hover:bg-transparent"
            : ""
        }
      `}
    >
      {children}
    </button>
  );
}