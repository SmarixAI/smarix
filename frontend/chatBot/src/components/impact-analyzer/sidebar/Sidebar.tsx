"use client";

import { useState, useMemo } from "react";
import FileTree from "./FileTree";
import { Search, Flame, AlertTriangle } from "lucide-react";

interface Props {
  tree: any[];
  onSelectFile: (path: string) => void;
}

export default function Sidebar({ tree, onSelectFile }: Props) {
  const [search, setSearch] = useState("");
  const [showHighRiskFiles, setShowHighRiskFiles] = useState(false);
  const [showHighRiskSymbols, setShowHighRiskSymbols] = useState(false);

  // 🔍 Simple search filter (filters by file name match)
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

          {/* High Risk Files Icon */}
          <button
            onClick={() => {
              setShowHighRiskFiles(!showHighRiskFiles);
              setShowHighRiskSymbols(false);
            }}
            className={`p-2 rounded-md ${
              showHighRiskFiles ? "bg-[#3C3C3C]" : "hover:bg-[#2A2D2E]"
            }`}
          >
            <Flame size={18} className="text-orange-400" />
          </button>

          {/* High Risk Symbols Icon */}
          <button
            onClick={() => {
              setShowHighRiskSymbols(!showHighRiskSymbols);
              setShowHighRiskFiles(false);
            }}
            className={`p-2 rounded-md ${
              showHighRiskSymbols ? "bg-[#3C3C3C]" : "hover:bg-[#2A2D2E]"
            }`}
          >
            <AlertTriangle size={18} className="text-yellow-400" />
          </button>

        </div>
      </div>

      {/* 📂 File Tree */}
      <div className="flex-1 overflow-auto p-3">
        <FileTree tree={filteredTree} onSelectFile={onSelectFile} />
      </div>
    </div>
  );
}