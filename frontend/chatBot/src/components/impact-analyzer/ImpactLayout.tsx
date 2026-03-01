"use client";

import { useEffect, useState } from "react";
import Sidebar from "./sidebar/Sidebar";
import CodeViewer from "./main/CodeViewer";
import SymbolView from "./main/SymbolView";
import ImpactPanel from "./impact/ImpactPanel";
import GraphEditorView from "./main/GraphEditorView";

const API_BASE = "http://localhost:8000";


type ViewMode =
  | "code"
  | "file-symbol"
  | "project-graph"
  | "file-graph";

export default function ImpactLayout() {
  const [tree, setTree] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const [fileContent, setFileContent] = useState<string>("");
  const [impactData, setImpactData] = useState<any>(null);
  const [fileSymbols, setFileSymbols] = useState<any>(null);

  const [projectGraphData, setProjectGraphData] = useState<any>(null);
  const [fileGraphData, setFileGraphData] = useState<any>(null);

  const [loadingProjectGraph, setLoadingProjectGraph] = useState(false);
  const [loadingFileGraph, setLoadingFileGraph] = useState(false);

  const [extractorId, setExtractorId] = useState<string>("");
  const [repoId, setRepoId] = useState<string>("");

  const [viewMode, setViewMode] = useState<ViewMode>("code");

  // ================= Load Project Structure =================
  useEffect(() => {
    if (!extractorId || !repoId) return;

    async function loadStructure() {
      try {
        const res = await fetch(
          `${API_BASE}/impact/${extractorId}/repos/${repoId}/project-structure`
        );

        if (!res.ok) throw new Error("Failed to fetch structure");

        const data = await res.json();
        setTree(Array.isArray(data.tree) ? data.tree : []);
      } catch {
        console.error("Failed to load project structure");
        setTree([]);
      }
    }

    loadStructure();
  }, [extractorId, repoId]);

  // ================= Load File Data =================
  useEffect(() => {
    if (!selectedFile) return;

    setViewMode("code");
    setFileGraphData(null);

    async function loadFileData() {
      try {
        const encodedPath = encodeURIComponent(selectedFile);

        const [contentRes, impactRes, symbolRes] = await Promise.all([
          fetch(
            `${API_BASE}/impact/${extractorId}/repos/${repoId}/file-content?path=${encodedPath}`
          ),
          fetch(
            `${API_BASE}/impact/${extractorId}/repos/${repoId}/file-impact?path=${encodedPath}`
          ),
          fetch(
            `${API_BASE}/impact/${extractorId}/repos/${repoId}/file-symbols?path=${encodedPath}`
          ),
        ]);

        if (!contentRes.ok || !impactRes.ok || !symbolRes.ok) {
          throw new Error("File data request failed");
        }

        const contentData = await contentRes.json();
        const impactData = await impactRes.json();
        const symbolData = await symbolRes.json();

        setFileContent(contentData.content ?? "");
        setImpactData(impactData);
        setFileSymbols(symbolData);
      } catch (err) {
        console.error("Failed to load file data");
        setFileContent("");
        setImpactData(null);
        setFileSymbols(null);
      }
    }

    loadFileData();
  }, [selectedFile, extractorId, repoId]);

  // ================= File Graph =================
  async function loadFileGraph() {
    if (!selectedFile) return;

    if (viewMode === "file-graph") {
      setViewMode("code");
      return;
    }

    // Prevent stale graph bug
    if (
      fileGraphData &&
      fileGraphData.center === selectedFile
    ) {
      setViewMode("file-graph");
      return;
    }

    try {
      setLoadingFileGraph(true);

      const encodedPath = encodeURIComponent(selectedFile);

      const res = await fetch(
        `${API_BASE}/impact/${extractorId}/repos/${repoId}/file-graph?path=${encodedPath}`
      );

      if (!res.ok) throw new Error("File graph request failed");

      const data = await res.json();

      setFileGraphData(data);
      setViewMode("file-graph");
    } catch {
      console.error("Failed to load file graph");
    } finally {
      setLoadingFileGraph(false);
    }
  }

  // ================= Project Graph =================
  async function loadProjectGraph() {
    if (viewMode === "project-graph") {
      setViewMode("code");
      return;
    }

    // Cache project graph
    if (projectGraphData) {
      setViewMode("project-graph");
      return;
    }

    try {
      setLoadingProjectGraph(true);

      const res = await fetch(
        `${API_BASE}/impact/${extractorId}/repos/${repoId}/project-graph`
      );

      if (!res.ok) throw new Error("Project graph request failed");

      const data = await res.json();

      setProjectGraphData(data);
      setViewMode("project-graph");
    } catch {
      console.error("Failed to load project graph");
    } finally {
      setLoadingProjectGraph(false);
    }
  }

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
        }}
      />

      {/* ================= CENTER ================= */}
      <div className="flex flex-col flex-1 min-w-0 border-l border-r border-[#1F2937]">

        {/* ================= HEADER ================= */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#0F172A] border-b border-[#1F2937]">

          <div className="min-w-0">
            <div className="text-sm font-semibold text-white truncate">
              {selectedFile
                ? selectedFile.split("/").pop()
                : "No file selected"}
            </div>
            {selectedFile && (
              <div className="text-xs text-gray-500 truncate max-w-[500px]">
                {selectedFile}
              </div>
            )}
          </div>

          <div className="flex items-center bg-[#111827] border border-[#1F2937] rounded-xl p-1">

            <SegmentButton
              active={viewMode === "code"}
              onClick={() => setViewMode("code")}
              disabled={!selectedFile}
            >
              Code
            </SegmentButton>

            <SegmentButton
              active={viewMode === "file-symbol"}
              onClick={() =>
                setViewMode(
                  viewMode === "file-symbol" ? "code" : "file-symbol"
                )
              }
              disabled={!selectedFile}
            >
              Symbols
            </SegmentButton>

            <SegmentButton
              active={viewMode === "file-graph"}
              onClick={loadFileGraph}
              disabled={!selectedFile}
            >
              File Graph
            </SegmentButton>

            <SegmentButton
              active={viewMode === "project-graph"}
              onClick={loadProjectGraph}
            >
              Project Graph
            </SegmentButton>

          </div>
        </div>

        {/* ================= CONTENT ================= */}
        <div className="flex-1 min-h-0 flex">

          {viewMode === "code" && (
            <CodeViewer
              content={fileContent}
              fileName={selectedFile ?? undefined}
            />
          )}

          {viewMode === "file-symbol" && fileSymbols && (
            <SymbolView fileSymbols={fileSymbols} />
          )}

          {viewMode === "project-graph" && (
            <>
              {loadingProjectGraph && (
                <CenteredLoader text="Loading project graph..." />
              )}
              {!loadingProjectGraph && projectGraphData && (
                <GraphEditorView graphData={projectGraphData} />
              )}
            </>
          )}

          {viewMode === "file-graph" && (
            <>
              {loadingFileGraph && (
                <CenteredLoader text="Loading file graph..." />
              )}
              {!loadingFileGraph && fileGraphData && (
                <GraphEditorView graphData={fileGraphData} />
              )}
            </>
          )}

        </div>
      </div>

      {/* ================= RIGHT PANEL ================= */}
      <ImpactPanel
        extractorId={extractorId}
        repoId={repoId}
        selectedFile={selectedFile}
        impact={impactData}
      />
    </div>
  );
}

/* ================= UI COMPONENTS ================= */

function SegmentButton({
  children,
  active,
  onClick,
  disabled,
}: any) {
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
            ? "opacity-40 cursor-not-allowed hover:bg-transparent hover:text-gray-400"
            : ""
        }
      `}
    >
      {children}
    </button>
  );
}

function CenteredLoader({ text }: any) {
  return (
    <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
      {text}
    </div>
  );
}