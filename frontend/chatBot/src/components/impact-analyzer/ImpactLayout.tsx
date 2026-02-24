"use client";

import { useEffect, useState } from "react";
import Sidebar from "./sidebar/Sidebar";
import CodeViewer from "./main/CodeViewer";
import SymbolView from "./main/SymbolView";
import ImpactPanel from "./impact/ImpactPanel";
import GraphEditorView from "./main/GraphEditorView";

const REPO_ID = "0550c1f7c52e3807222e968766843d27";
const COMMIT_HASH = "c34d6e81fd8e405e6d4178bf24b364918811ef17";

export default function ImpactLayout() {
  const [tree, setTree] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const [fileContent, setFileContent] = useState<string>("");
  const [impactData, setImpactData] = useState<any>(null);
  const [fileSymbols, setFileSymbols] = useState<any>(null);
  const [projectGraphData, setProjectGraphData] = useState<any>(null);
  const [loadingProjectGraph, setLoadingProjectGraph] = useState(false);
  const [fileGraphData, setFileGraphData] = useState<any>(null);
  const [loadingFileGraph, setLoadingFileGraph] = useState(false);

  const [viewMode, setViewMode] = useState<
    "code" | "file-symbol" | "project-graph" | "file-graph"
  >("code");

  // ---------------- Load Project Structure ----------------
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

  // ---------------- Load File Data ----------------
  useEffect(() => {
    if (!selectedFile) return;

    setViewMode("code");

    // 🔥 RESET GRAPH DATA WHEN FILE CHANGES
    setFileGraphData(null);

    async function loadFileData() {
      const contentRes = await fetch(
        `http://localhost:8000/impact/file-content/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
      );
      const contentData = await contentRes.json();
      setFileContent(contentData.content);

      const impactRes = await fetch(
        `http://localhost:8000/impact/file-impact/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
      );
      setImpactData(await impactRes.json());

      const symbolRes = await fetch(
        `http://localhost:8000/impact/file-symbols/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
      );
      setFileSymbols(await symbolRes.json());
    }

    loadFileData();
  }, [selectedFile]);

  async function loadFileGraph() {

  if (!selectedFile) return;

  // 🔁 Toggle back if already open
  if (viewMode === "file-graph") {
    setViewMode("code");
    return;
  }

  // 🚀 Cache optimization
  if (fileGraphData) {
    setViewMode("file-graph");
    return;
  }

  try {
    setLoadingFileGraph(true);

    const res = await fetch(
      `http://localhost:8000/impact/file-graph/${REPO_ID}/${COMMIT_HASH}?path=${selectedFile}`
    );

    if (!res.ok) {
      console.error("File graph request failed:", res.status);
      return;
    }

    const data = await res.json();
    setFileGraphData(data);
    setViewMode("file-graph");

  } catch (err) {
    console.error("Failed to load file graph");
  } finally {
    setLoadingFileGraph(false);
  }
}

  async function loadProjectGraph() {

  // 🔁 Toggle Back If Already Open
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

  } catch (err) {
    console.error("Failed to load project graph");
  } finally {
    setLoadingProjectGraph(false);
  }
}

  return (
    <div className="flex h-screen text-white bg-[#1E1E1E]">

      {/* LEFT */}
      <Sidebar
        tree={tree}
        repoId={REPO_ID}
        commitHash={COMMIT_HASH}
        onSelectFile={setSelectedFile}
      />

      {/* MIDDLE */}
      <div className="flex flex-col flex-1 min-w-0 border-l border-r border-[#2D2D2D]">

        {/* TOP BAR */}
        <div className="flex items-center justify-between bg-[#252526] px-5 py-3 border-b border-[#2D2D2D]">

          <div>
            <div className="text-sm font-semibold text-white">
              {selectedFile
                ? selectedFile.split("/").pop()
                : "No file selected"}
            </div>
            {selectedFile && (
              <div className="text-xs text-gray-400 truncate max-w-[400px]">
                {selectedFile}
              </div>
            )}
          </div>

          {/* Only File Symbol toggle */}
          <div className="flex gap-2">

  {/* File Symbols Button */}
  <button
    onClick={() =>
      setViewMode((prev) =>
        prev === "file-symbol" ? "code" : "file-symbol"
      )
    }
    disabled={!selectedFile}
    className={`px-3 py-1.5 text-xs rounded transition
      ${
        viewMode === "file-symbol"
          ? "bg-blue-600 text-white"
          : "bg-[#2D2D2D] text-gray-300 hover:bg-[#3A3D41]"
      }
      ${!selectedFile ? "opacity-50 cursor-not-allowed hover:bg-[#2D2D2D]" : ""}
    `}
  >
    File Symbols
  </button>

    {/* File Graph Button */}
  <button
    onClick={loadFileGraph}
    disabled={!selectedFile}
    className={`px-3 py-1.5 text-xs rounded transition
      ${
        viewMode === "file-graph"
          ? "bg-green-600 text-white"
          : "bg-[#2D2D2D] text-gray-300 hover:bg-[#3A3D41]"
      }
      ${!selectedFile ? "opacity-50 cursor-not-allowed" : ""}
    `}
  >
    File Graph
  </button>

  {/* Project Graph Button */}
  <button
    onClick={loadProjectGraph}
    className={`px-3 py-1.5 text-xs rounded transition
      ${
        viewMode === "project-graph"
          ? "bg-purple-600 text-white"
          : "bg-[#2D2D2D] text-gray-300 hover:bg-[#3A3D41]"
      }`}
  >
    Project Graph
  </button>



</div>
        </div>

        {viewMode === "code" && (
          <CodeViewer content={fileContent} />
        )}

        {viewMode === "file-symbol" && (
          <SymbolView fileSymbols={fileSymbols} />
        )}

        {viewMode === "project-graph" && (
        <>
          {loadingProjectGraph && (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              Loading project graph...
            </div>
          )}

          {!loadingProjectGraph && projectGraphData && (
            <GraphEditorView graphData={projectGraphData} />
          )}
        </>
      )}

      {viewMode === "file-graph" && (
        <>
          {loadingFileGraph && (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              Loading file graph...
            </div>
          )}

          {!loadingFileGraph && fileGraphData && (
            <GraphEditorView graphData={fileGraphData} />
          )}
        </>
      )}
      </div>

      {/* RIGHT */}
      <ImpactPanel
        repoId={REPO_ID}
        commitHash={COMMIT_HASH}
        selectedFile={selectedFile}
        impact={impactData}
      />

    </div>
  );
}