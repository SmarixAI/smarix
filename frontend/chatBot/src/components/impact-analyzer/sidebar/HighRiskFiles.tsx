"use client";

import { useState, useRef, useEffect } from "react";
import { FileNode } from "@/app/impact-analyzer/types";

interface Props {
  files: FileNode[];
  onSelectFile: (file: FileNode) => void;
}

export default function HighRiskFiles({ files, onSelectFile }: Props) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const highRisk = files.filter((f) => f.riskScore > 80);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative mt-6" ref={containerRef}>
      
      {/* Toggle Button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="w-full text-left text-xs uppercase text-red-400 bg-[#111827] px-3 py-2 rounded-lg hover:bg-[#1F2937] transition"
      >
        High Risk Files ({highRisk.length})
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 mt-2 w-full bg-[#1E1E1E] border border-[#1F2937] rounded-lg shadow-lg max-h-60 overflow-auto">
          {highRisk.length === 0 && (
            <div className="px-3 py-2 text-sm text-gray-500">
              No high risk files
            </div>
          )}

          {highRisk.map((file) => (
            <div
              key={file.id}
              onClick={() => {
                onSelectFile(file);
                setOpen(false);
              }}
              className="px-3 py-2 text-sm text-red-300 hover:bg-[#2A2D2E] cursor-pointer transition"
            >
              {file.name}
              <span className="float-right text-xs text-red-500">
                {file.riskScore}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}