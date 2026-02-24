"use client";

import { useState } from "react";

interface Node {
  type: "file" | "folder";
  name: string;
  path: string;
  children?: Node[];
}

interface Props {
  tree: Node[];
  onSelectFile: (path: string) => void;
  selectedFile?: string | null;
  level?: number;
}

export default function FileTree({
  tree,
  onSelectFile,
  selectedFile,
  level = 0,
}: Props) {
  return (
    <div>
      {tree.map((node) => (
        <TreeNode
          key={node.path}
          node={node}
          onSelectFile={onSelectFile}
          selectedFile={selectedFile}
          level={level}
        />
      ))}
    </div>
  );
}

function TreeNode({
  node,
  onSelectFile,
  selectedFile,
  level,
}: {
  node: Node;
  onSelectFile: (path: string) => void;
  selectedFile?: string | null;
  level: number;
}) {
  const [isOpen, setIsOpen] = useState(true);

  const isActive = selectedFile === node.path;

  const paddingLeft = 12 + level * 14;

  if (node.type === "folder") {
    return (
      <div>
        <div
          style={{ paddingLeft }}
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1 text-sm text-gray-300 hover:bg-[#2A2D2E] cursor-pointer select-none py-1"
        >
          <span className="text-xs w-4">
            {isOpen ? "▾" : "▸"}
          </span>

          <span>{isOpen ? "📂" : "📁"}</span>

          <span className="truncate">{node.name}</span>
        </div>

        {isOpen && node.children && (
          <FileTree
            tree={node.children}
            onSelectFile={onSelectFile}
            selectedFile={selectedFile}
            level={level + 1}
          />
        )}
      </div>
    );
  }

  return (
    <div
      style={{ paddingLeft }}
      onClick={() => onSelectFile(node.path)}
      className={`flex items-center gap-2 text-sm py-1 cursor-pointer truncate
        ${
          isActive
            ? "bg-[#37373D] text-white"
            : "text-gray-400 hover:bg-[#2A2D2E]"
        }`}
    >
      <span className="w-4" />
      <span>📄</span>
      <span className="truncate">{node.name}</span>
    </div>
  );
}