"use client";

import { useState, useMemo, useEffect } from "react";
import FileTree from "./FileTree";
import { Search, Flame } from "lucide-react";

interface Props {
  tree: any[];
  repoId: string;
  commitHash: string;
  onSelectFile: (path: string) => void;
}

export default function Sidebar({
  tree,
  repoId,
  commitHash,
  onSelectFile,
}: Props) {
  const [search, setSearch] = useState("");
  const [showHighRiskFiles, setShowHighRiskFiles] = useState(false);

  const [highRiskFiles, setHighRiskFiles] = useState<any[]>([]);
  const [loadingHighRisk, setLoadingHighRisk] = useState(false);

  // --------------------------------------------
  // 🔥 Load High Risk Files
  // --------------------------------------------
  useEffect(() => {
    if (!showHighRiskFiles) return;

    async function loadHighRiskFiles() {
      try {
        setLoadingHighRisk(true);

        const res = await fetch(
          `http://localhost:8000/impact/high-risk-files/${repoId}/${commitHash}`
        );

        if (!res.ok) throw new Error("Failed to fetch");

        const data = await res.json();
        setHighRiskFiles(data.high_risk_files || []);
      } catch (err) {
        console.error("Failed to load high risk files");
        setHighRiskFiles([]);
      } finally {
        setLoadingHighRisk(false);
      }
    }

    loadHighRiskFiles();
  }, [showHighRiskFiles, repoId, commitHash]);

  // --------------------------------------------
  // 🔍 Search Filter
  // --------------------------------------------
  const filteredTree = useMemo(() => {
    if (!search) return tree;

    function filterNodes(nodes: any[]): any[] {
      return nodes
        .map((node) => {
          if (node.type === "file") {
            if (node.name.toLowerCase().includes(search.toLowerCase())) {
              return node;
            }
            return null;
          }

          if (node.type === "folder") {
            const children = filterNodes(node.children || []);
            if (children.length > 0) {
              return { ...node, children };
            }
            return null;
          }

          return null;
        })
        .filter(Boolean);
    }

    return filterNodes(tree);
  }, [search, tree]);

  // --------------------------------------------
  // 🎨 Severity Color Helper
  // --------------------------------------------
  function getSeverityColor(severity: string) {
    if (severity === "HIGH") return "text-red-400";
    if (severity === "MEDIUM") return "text-yellow-400";
    return "text-green-400";
  }

  return (
    <div className="w-80 border-r border-[#2D2D2D] bg-[#1E1E1E] flex flex-col">

      {/* 🔎 Search + Icons */}
      <div className="p-3 border-b border-[#2D2D2D]">
        <div className="flex items-center gap-2">

          {/* Search Input */}
          <div className="flex items-center bg-[#252526] px-2 py-1 rounded-md flex-1">
            <Search size={16} className="text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent outline-none text-sm ml-2 w-full text-gray-200"
            />
          </div>

          {/* High Risk Files Toggle */}
          <button
            onClick={() => setShowHighRiskFiles((prev) => !prev)}
            className={`p-2 rounded-md ${
              showHighRiskFiles
                ? "bg-[#3C3C3C]"
                : "hover:bg-[#2A2D2E]"
            }`}
          >
            <Flame size={18} className="text-orange-400" />
          </button>
        </div>
      </div>

      {/* 📂 Content Area */}
      <div className="flex-1 overflow-auto p-3">

        {/* 🔥 High Risk Files Mode */}
        {showHighRiskFiles ? (
          <>
            {loadingHighRisk && (
              <div className="text-gray-400 text-sm">
                Loading high risk files...
              </div>
            )}

            {!loadingHighRisk && highRiskFiles.length === 0 && (
              <div className="text-gray-500 text-sm">
                No high risk files found.
              </div>
            )}

            {!loadingHighRisk &&
              highRiskFiles.map((file) => (
                <div
                  key={file.file}
                  onClick={() => onSelectFile(file.file)}
                  className="mb-3 p-3 bg-[#252526] rounded hover:bg-[#2A2D2E] cursor-pointer transition"
                >
                  <div className="flex justify-between">
                    <div className="text-white text-sm truncate">
                      {file.name}
                    </div>
                    <div
                      className={`text-xs font-semibold ${getSeverityColor(
                        file.severity
                      )}`}
                    >
                      {file.severity}
                    </div>
                  </div>

                  <div className="text-xs text-gray-400 mt-1">
                    Blast: {file.blast_radius} | Fan-In: {file.fan_in} | Fan-Out: {file.fan_out}
                  </div>
                </div>
              ))}
          </>
        ) : (
          <FileTree tree={filteredTree} onSelectFile={onSelectFile} />
        )}
      </div>
    </div>
  );
}