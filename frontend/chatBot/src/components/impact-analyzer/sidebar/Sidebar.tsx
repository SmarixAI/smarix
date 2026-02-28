"use client";

import { useState, useMemo, useEffect, useRef } from "react";
import FileTree from "./FileTree";
import { Search, Flame } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface Props {
  tree: any[];
  extractorId: string;
  repoId: string;
  onSelectFile: (path: string) => void;
  onProjectChange: (extractorId: string, repoId: string) => void;
}

export default function Sidebar({
  tree,
  extractorId,
  repoId,
  onSelectFile,
  onProjectChange,
}: Props) {
  const [search, setSearch] = useState("");

  // 🔥 Controlled High Risk Panel
  const [highRiskOpen, setHighRiskOpen] = useState(false);

  const [highRiskFiles, setHighRiskFiles] = useState<any[]>([]);
  const [loadingHighRisk, setLoadingHighRisk] = useState(false);
  const [highRiskLoaded, setHighRiskLoaded] = useState(false);

  const highRiskRef = useRef<HTMLDivElement>(null);

  const [extractors, setExtractors] = useState<string[]>([]);
  const [repos, setRepos] = useState<string[]>([]);
  const [projectsData, setProjectsData] = useState<any[]>([]);

  // ---------------------------------------------------
  // 🔁 Reset High Risk Cache When Repo Changes
  // ---------------------------------------------------
  useEffect(() => {
    setHighRiskFiles([]);
    setHighRiskLoaded(false);
    setHighRiskOpen(false);
  }, [repoId]);

  // ---------------------------------------------------
  // 🔥 Load High Risk Files (Lazy + Cached)
  // ---------------------------------------------------
  useEffect(() => {
    if (!highRiskOpen) return;
    if (highRiskLoaded) return;

    async function loadHighRiskFiles() {
      try {
        setLoadingHighRisk(true);

        const res = await fetch(
          `${API_BASE}/impact/${extractorId}/repos/${repoId}/high-risk-files`
        );

        if (!res.ok) {
          throw new Error("Failed to fetch high risk files");
        }

        const data = await res.json();

        setHighRiskFiles(
          Array.isArray(data.high_risk_files)
            ? data.high_risk_files
            : []
        );

        setHighRiskLoaded(true);
      } catch {
        console.error("Failed to load high risk files");
        setHighRiskFiles([]);
        setHighRiskLoaded(true);
      } finally {
        setLoadingHighRisk(false);
      }
    }

    loadHighRiskFiles();
  }, [highRiskOpen, extractorId, repoId, highRiskLoaded]);

  // ---------------------------------------------------
  // 🔒 Close When Clicking Outside
  // ---------------------------------------------------
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        highRiskRef.current &&
        !highRiskRef.current.contains(event.target as Node)
      ) {
        setHighRiskOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
  }, []);

    

  useEffect(() => {
    async function loadProjects() {
      try {
        const res = await fetch(`${API_BASE}/projects`);
        const data = await res.json();

        if (!Array.isArray(data)) return;

        setProjectsData(data);

        const extractorNames = data.map((item) => item.extractor);
        setExtractors(extractorNames);

        if (data.length > 0) {
          const firstExtractor = data[0].extractor;
          const firstRepo = data[0].repos?.[0] || "";

          setRepos(data[0].repos || []);

          if (firstRepo) {
            onProjectChange(firstExtractor, firstRepo);
          }
        }
      } catch (err) {
        console.error("Failed to load projects", err);
        setExtractors([]);
      }
    }

    loadProjects();
  }, []);







  // ---------------------------------------------------
  // 🔍 Recursive Safe Search Filter
  // ---------------------------------------------------
  const filteredTree = useMemo(() => {
    if (!search) return Array.isArray(tree) ? tree : [];

    const lowerSearch = search.toLowerCase();

    function filterNodes(nodes: any[]): any[] {
      return nodes
        .map((node) => {
          if (node.type === "file") {
            if (node.name?.toLowerCase().includes(lowerSearch)) {
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

    return filterNodes(Array.isArray(tree) ? tree : []);
  }, [search, tree]);

  // ---------------------------------------------------
  // 🎨 Severity Color Mapping
  // ---------------------------------------------------
  function getSeverityColor(severity: string) {
    if (severity === "HIGH") return "text-red-400";
    if (severity === "MEDIUM") return "text-yellow-400";
    return "text-green-400";
  }

  return (
    <div className="w-80 border-r border-[#1F2937] bg-[#0F172A] flex flex-col">

      {/* ================================================= */}
      {/* 🗂 PROJECT SELECTOR */}
      {/* ================================================= */}
      <div className="p-3 border-b border-[#1F2937] space-y-2">

        {/* Extractor Dropdown */}
        <select
          value={extractorId}
          onChange={(e) => {
            const newExtractor = e.target.value;

            const found = projectsData.find(
              (item: any) => item.extractor === newExtractor
            );

            const newRepos = found?.repos || [];
            setRepos(newRepos);

            if (newRepos.length > 0) {
              // DO NOT trigger structure yet
              onProjectChange(newExtractor, newRepos[0]);
            } else {
              onProjectChange(newExtractor, "");
            }
          }}
          className="w-full bg-[#111827] text-gray-200 text-sm p-2 rounded-md border border-[#1F2937]"
        >
          <option value="">Select Extractor</option>
          {extractors.map((ext) => (
            <option key={ext} value={ext}>
              {ext}
            </option>
          ))}
        </select>

        {/* Repo Dropdown */}
        <select
          value={repoId}
          onChange={(e) => {
            const repo = e.target.value;
            onProjectChange(extractorId, repo);
          }}
          className="w-full bg-[#111827] text-gray-200 text-sm p-2 rounded-md border border-[#1F2937]"
          disabled={!extractorId}
        >
          <option value="">Select Repo</option>
          {repos.map((repo) => (
            <option key={repo} value={repo}>
              {repo}
            </option>
          ))}
        </select>
      </div>

      {/* ================================================= */}
      {/* 🔎 SEARCH + HIGH RISK SECTION */}
      {/* ================================================= */}
      <div className="p-3 border-b border-[#1F2937] relative">
        <div className="flex items-center gap-2">

          {/* Search Input */}
          <div className="relative flex items-center bg-[#111827] px-2 py-1 rounded-md flex-1 border border-[#1F2937]">

            <Search size={16} className="text-gray-400" />

            <input
              type="text"
              placeholder="Search files..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent outline-none text-sm ml-2 w-full text-gray-200 pr-6"
            />

            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2 text-gray-400 hover:text-white transition"
              >
                ✕
              </button>
            )}

          </div>

          {/* 🔥 High Risk Click Icon */}
          <div className="relative group" ref={highRiskRef}>
            <div
              onClick={() => setHighRiskOpen((prev) => !prev)}
              className="w-9 h-9 flex items-center justify-center rounded-lg 
                        hover:bg-[#162036] transition cursor-pointer"
            >
              <Flame size={18} className="text-orange-400" />
            </div>

            {/* 🔥 Tooltip */}
            <div
              className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2
                        px-3 py-1 text-xs rounded-md
                        bg-[#111827] border border-[#1F2937]
                        text-gray-300 whitespace-nowrap
                        opacity-0 group-hover:opacity-100
                        transition-opacity duration-200
                        pointer-events-none z-50"
            >
              View High Risk Files
            </div>

            {/* 🔥 Floating High Risk Panel */}
            {highRiskOpen && (
              <div className="absolute left-12 top-0 w-80 
                              bg-[#111827] border border-[#1F2937]
                              rounded-xl shadow-2xl p-4 z-50">

                <div className="text-xs uppercase tracking-wide text-orange-400 mb-3">
                  High Risk Files
                </div>

                {loadingHighRisk && (
                  <div className="text-gray-400 text-sm">
                    Loading...
                  </div>
                )}

                {!loadingHighRisk &&
                  highRiskFiles.length === 0 && (
                    <div className="text-gray-500 text-sm">
                      No high risk files found.
                    </div>
                  )}

                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {highRiskFiles.map((file) => (
                    <div
                      key={file.file}
                      onClick={() => {
                        onSelectFile(file.file);
                        setHighRiskOpen(false);
                      }}
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

      {/* ================================================= */}
      {/* 📂 FILE TREE SECTION */}
      {/* ================================================= */}
      <div className="flex-1 overflow-auto p-3">

        {filteredTree.length === 0 ? (
          <div className="text-gray-500 text-sm p-4">
            No files found.
          </div>
        ) : (
          <FileTree
            tree={filteredTree}
            onSelectFile={onSelectFile}
          />
        )}

      </div>
    </div>
  );
}