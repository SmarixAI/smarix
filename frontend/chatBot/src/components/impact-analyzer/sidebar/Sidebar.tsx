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
  const [hoverHighRisk, setHoverHighRisk] = useState(false);

  const [highRiskFiles, setHighRiskFiles] = useState<any[]>([]);
  const [loadingHighRisk, setLoadingHighRisk] = useState(false);

  // --------------------------------------------
  // 🔥 Load High Risk Files (On Hover)
  // --------------------------------------------
  useEffect(() => {
    if (!hoverHighRisk) return;
    if (highRiskFiles.length > 0) return; // cache

    async function loadHighRiskFiles() {
      try {
        setLoadingHighRisk(true);

        const res = await fetch(
          `http://localhost:8000/impact/high-risk-files/${repoId}/${commitHash}`
        );

        const data = await res.json();
        setHighRiskFiles(data.high_risk_files || []);
      } catch {
        console.error("Failed to load high risk files");
      } finally {
        setLoadingHighRisk(false);
      }
    }

    loadHighRiskFiles();
  }, [hoverHighRisk, repoId, commitHash]);

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
  // 🎨 Severity Color
  // --------------------------------------------
  function getSeverityColor(severity: string) {
    if (severity === "HIGH") return "text-red-400";
    if (severity === "MEDIUM") return "text-yellow-400";
    return "text-green-400";
  }

  return (
    <div className="w-80 border-r border-[#1F2937] bg-[#0F172A] flex flex-col">

      {/* 🔎 Search + Flame */}
      <div className="p-3 border-b border-[#1F2937] relative">
        <div className="flex items-center gap-2">

          {/* Search */}
          <div className="flex items-center bg-[#111827] px-2 py-1 rounded-md flex-1 border border-[#1F2937]">
            <Search size={16} className="text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent outline-none text-sm ml-2 w-full text-gray-200"
            />
          </div>

          {/* 🔥 High Risk Hover Icon */}
          <div
            className="relative"
            onMouseEnter={() => setHoverHighRisk(true)}
            onMouseLeave={() => setHoverHighRisk(false)}
          >
            <div className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[#162036] transition cursor-pointer">
              <Flame size={18} className="text-orange-400" />
            </div>

            {/* 🔥 Floating Panel */}
            {hoverHighRisk && (
              <div className="absolute left-12 top-0 w-80 
                              bg-[#111827] border border-[#1F2937]
                              rounded-xl shadow-2xl p-4 z-50
                              animate-fade-in">

                <div className="text-xs uppercase tracking-wide text-orange-400 mb-3">
                  High Risk Files
                </div>

                {loadingHighRisk && (
                  <div className="text-gray-400 text-sm">
                    Loading...
                  </div>
                )}

                {!loadingHighRisk && highRiskFiles.length === 0 && (
                  <div className="text-gray-500 text-sm">
                    No high risk files found.
                  </div>
                )}

                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {highRiskFiles.map((file) => (
                    <div
                      key={file.file}
                      onClick={() => onSelectFile(file.file)}
                      className="px-3 py-2 rounded-lg hover:bg-orange-500/10 
                                 cursor-pointer transition"
                    >
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-200 truncate max-w-[160px]">
                          {file.name}
                        </span>
                        <span
                          className={`text-xs font-semibold ${getSeverityColor(
                            file.severity
                          )}`}
                        >
                          {file.severity}
                        </span>
                      </div>

                      <div className="text-xs text-gray-500 mt-1">
                        Blast: {file.blast_radius} • 
                        Fan-In: {file.fan_in} • 
                        Fan-Out: {file.fan_out}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* 📂 File Tree */}
      <div className="flex-1 overflow-auto p-3">
        <FileTree tree={filteredTree} onSelectFile={onSelectFile} />
      </div>
    </div>
  );
}