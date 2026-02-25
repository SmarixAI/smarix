"use client";

import { useEffect, useState } from "react";
import Sidebar from "./sidebar/Sidebar";
import CodeViewer from "./main/CodeViewer";
import SymbolView from "./main/SymbolView";
import ImpactPanel from "./impact/ImpactPanel";
import GraphEditorView from "./main/GraphEditorView";

const REPO_ID = "0550c1f7c52e3807222e968766843d27";
const COMMIT_HASH = "c34d6e81fd8e405e6d4178bf24b364918811ef17";

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

  const [viewMode, setViewMode] = useState<ViewMode>("code");

  // ================= Load Project Structure =================
  useEffect(() => {
    async function loadStructure() {
      const res = await fetch(
        `http://localhost:8000/impact/project-structure/${REPO_ID}/${COMMIT_HASH}`
      );
      const data = await res.json();
      setTree(data.tree);
    }

    loadStructure();
  }, []);

  // ================= Load File Data =================
  useEffect(() => {
    if (!selectedFile) return;

    setViewMode("code");
    setFileGraphData(null);

    async function loadFileData() {
      try {
        const [contentRes, impactRes, symbolRes] = await Promise.all([
          fetch(
            `http://localhost:8000/impact/file-content/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
          ),
          fetch(
            `http://localhost:8000/impact/file-impact/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
          ),
          fetch(
            `http://localhost:8000/impact/file-symbols/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
          ),
        ]);

        const contentData = await contentRes.json();
        setFileContent(contentData.content ?? "");

        setImpactData(await impactRes.json());
        setFileSymbols(await symbolRes.json());
      } catch (err) {
        console.error("Failed to load file data");
      }
    }

    loadFileData();
  }, [selectedFile]);

  // ================= File Graph =================
  async function loadFileGraph() {
    if (!selectedFile) return;

    if (viewMode === "file-graph") {
      setViewMode("code");
      return;
    }

    if (fileGraphData) {
      setViewMode("file-graph");
      return;
    }

    try {
      setLoadingFileGraph(true);

      const res = await fetch(
        `http://localhost:8000/impact/file-graph/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
      );

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

    try {
      setLoadingProjectGraph(true);

      const res = await fetch(
        `http://localhost:8000/impact/project-graph/${REPO_ID}/${COMMIT_HASH}`
      );

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
        repoId={REPO_ID}
        commitHash={COMMIT_HASH}
        onSelectFile={setSelectedFile}
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

          {/* Segmented Control */}
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
            <CodeViewer content={fileContent} />
          )}

          {viewMode === "file-symbol" && (
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
        repoId={REPO_ID}
        commitHash={COMMIT_HASH}
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