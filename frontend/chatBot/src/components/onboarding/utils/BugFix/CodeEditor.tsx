"use client";

import { useState, useEffect } from "react";
import {
  RotateCcw,
  Download,
  Loader2,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  FileCode,
  Maximize2,
  Minimize2,
  Sparkles,
  Play,
  AlertCircle,
  Code2,
  FileText,
} from "lucide-react";
import Editor from "@monaco-editor/react";
import { JetBrains_Mono, DM_Sans } from "next/font/google";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

interface FileChange {
  file_path: string;
  change_type: string;
  diff: string;
  before_code: string;
  after_code: string;
  statistics: {
    lines_added: number;
    lines_deleted: number;
    total_changes: number;
  };
}

interface PullRequest {
  pr_number: number;
  file_changes: FileChange[];
}

interface CodeEditorProps {
  prData?: PullRequest;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
  onEvaluationComplete?: (evaluationData: any) => void;
  repoName: string;
}

interface FileEditorState {
  [filePath: string]: string;
}

export default function CodeEditor({
  prData,
  isFullscreen,
  onToggleFullscreen,
  onEvaluationComplete,
  repoName,
}: CodeEditorProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<FileEditorState>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<
    "idle" | "submitting" | "evaluating" | "complete"
  >("idle");
  const [showFileList, setShowFileList] = useState(true);
  const [filesWidth, setFilesWidth] = useState(280);
  const [isResizingFiles, setIsResizingFiles] = useState(false);

  useEffect(() => {
    if (prData && prData.file_changes.length > 0) {
      const initialContents: FileEditorState = {};
      prData.file_changes.forEach((fileChange) => {
        initialContents[fileChange.file_path] = fileChange.before_code;
      });
      setFileContents(initialContents);
      setSelectedFile(prData.file_changes[0].file_path);
    }
  }, [prData]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingFiles) return;

      const container = document.querySelector(".code-editor-container");
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const newWidth = e.clientX - rect.left;

      const constrainedWidth = Math.max(200, Math.min(600, newWidth));
      setFilesWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizingFiles(false);
    };

    if (isResizingFiles) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizingFiles]);

  const getLanguageFromPath = (filePath: string): string => {
    const ext = filePath.split(".").pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      js: "javascript",
      jsx: "javascript",
      ts: "typescript",
      tsx: "typescript",
      py: "python",
      java: "java",
      cpp: "cpp",
      c: "c",
      cs: "csharp",
      go: "go",
      rs: "rust",
      php: "php",
      rb: "ruby",
      swift: "swift",
      kt: "kotlin",
      r: "r",
      sql: "sql",
      sh: "shell",
      bash: "shell",
      pl: "perl",
      lua: "lua",
      dart: "dart",
      scala: "scala",
      hs: "haskell",
      groovy: "groovy",
      pas: "pascal",
      md: "markdown",
      json: "json",
      xml: "xml",
      yaml: "yaml",
      yml: "yaml",
      html: "html",
      css: "css",
      scss: "scss",
      lock: "yaml",
      cmake: "cmake",
    };
    return langMap[ext || ""] || "plaintext";
  };

  const handleCodeChange = (filePath: string, value: string | undefined) => {
    if (value !== undefined) {
      setFileContents((prev) => ({
        ...prev,
        [filePath]: value,
      }));
    }
  };

  const handleReset = () => {
    if (prData) {
      const resetContents: FileEditorState = {};
      prData.file_changes.forEach((fileChange) => {
        resetContents[fileChange.file_path] = fileChange.before_code;
      });
      setFileContents(resetContents);
      setSubmissionStatus("idle");
    }
  };

  const handleDownload = () => {
    if (!selectedFile) return;
    const code = fileContents[selectedFile];
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = selectedFile.split("/").pop() || "code.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSubmitCode = async () => {
    if (!repoName) {
      alert("Error: Repository name is missing. Please refresh the page.");
      return;
    }

    setIsSubmitting(true);
    setSubmissionStatus("submitting");

    const controller = new AbortController();

    try {
      console.log("🚀 [Step 1] Submitting code...");
      const baseURL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const safePrNumber = Number(prData?.pr_number);

      const submissionData = {
        pr_number: safePrNumber,
        file_changes: Object.entries(fileContents).map(([filePath, code]) => ({
          file_path: filePath,
          submitted_code: code,
        })),
        timestamp: new Date().toISOString(),
      };

      const response = await fetch(
        `/api/onboarding/bugFix/challenges?repo=${encodeURIComponent(
          repoName,
        )}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(submissionData),
          signal: controller.signal,
        },
      );

      if (!response.ok) {
        throw new Error(`Submission save failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || "Submission failed");
      }

      console.log("✅ [Step 1] Code saved. ID:", result.submission_id);

      setSubmissionStatus("evaluating");
      setIsEvaluating(true);

      if (result.submission_id && safePrNumber) {
        console.log("🚀 [Step 2] Requesting evaluation from Python backend...");

        const evalEndpoint = `${baseURL}/evaluate-submission`;

        const evalResponse = await fetch(evalEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            submission_id: result.submission_id,
            pr_number: safePrNumber,
            repo_name: repoName,
          }),
          signal: controller.signal,
        });

        if (!evalResponse.ok) {
          const errText = await evalResponse.text();
          throw new Error(
            `Evaluation failed (${evalResponse.status}): ${errText}`,
          );
        }

        const evalResult = await evalResponse.json();
        console.log("✅ [Step 2] Evaluation received:", evalResult);

        setSubmissionStatus("complete");
        if (onEvaluationComplete) {
          onEvaluationComplete(evalResult);
        }
      }
    } catch (error: any) {
      console.error("❌ Submission Error:", error);

      if (error.name === "AbortError") {
        alert("Request timed out. The backend is taking too long to respond.");
      } else {
        alert(`Error: ${error.message || "Something went wrong."}`);
      }

      setSubmissionStatus("idle");
    } finally {
      setIsSubmitting(false);
      setIsEvaluating(false);
    }
  };

  const getFileIcon = (filePath: string) => {
    const ext = filePath.split(".").pop()?.toLowerCase();
    const iconMap: Record<string, { icon: string; color: string }> = {
      js: { icon: "JS", color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
      jsx: { icon: "JSX", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
      ts: { icon: "TS", color: "bg-blue-600/10 text-blue-600 border-blue-600/20" },
      tsx: { icon: "TSX", color: "bg-blue-600/10 text-blue-600 border-blue-600/20" },
      py: { icon: "PY", color: "bg-green-500/10 text-green-500 border-green-500/20" },
      java: { icon: "JAVA", color: "bg-orange-500/10 text-orange-500 border-orange-500/20" },
      dart: { icon: "DART", color: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20" },
      cpp: { icon: "CPP", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
      c: { icon: "C", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
      lock: { icon: "LOCK", color: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20" },
      json: { icon: "JSON", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
      yaml: { icon: "YAML", color: "bg-pink-500/10 text-pink-500 border-pink-500/20" },
      yml: { icon: "YML", color: "bg-pink-500/10 text-pink-500 border-pink-500/20" },
      cmake: { icon: "CMAKE", color: "bg-red-500/10 text-red-500 border-red-500/20" },
    };
    return iconMap[ext || ""] || { icon: "FILE", color: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20" };
  };

  if (!prData || prData.file_changes.length === 0) {
    return (
      <div className={`h-full flex items-center justify-center bg-[#1E1E1E] ${dmSans.className}`}>
        <div className="flex flex-col items-center justify-center py-20 px-8 text-center">
          <div className="w-20 h-20 bg-zinc-900 border border-zinc-800 rounded-2xl flex items-center justify-center mb-6">
            <FileCode className="w-10 h-10 text-zinc-600" />
          </div>
          <h3 className="font-semibold text-lg text-zinc-200 mb-2">
            No Code Available
          </h3>
          <p className="text-sm text-zinc-500 max-w-sm">
            Select a challenge from the list to start coding
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col bg-[#1E1E1E] ${dmSans.className}`}>
      {/* SLEEK HEADER */}
      <div className="px-4 py-2.5 border-b border-white/5 bg-[#1F2023] flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center">
              <Code2 className="w-4 h-4 text-white" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-200">
              Code Editor
            </h3>
          </div>
          
          <div className="flex items-center gap-2">
            {onToggleFullscreen && (
              <button
                onClick={onToggleFullscreen}
                className="p-2 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-all"
                title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}
            <button
              onClick={handleReset}
              disabled={isSubmitting}
              className="p-2 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Reset Code"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={handleDownload}
              disabled={!selectedFile || isSubmitting}
              className="p-2 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Download File"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* EDITOR AREA */}
      <div className="flex flex-1 min-h-0 code-editor-container">

        {/* FILES RESIZER - Softer interactive state */}
        {/* FILE SIDEBAR - Relaxed Charcoal Slate with Vertical Tiled Label when closed */}
        <div
          className={`flex flex-col border-r border-white/5 overflow-hidden flex-shrink-0 transition-all duration-300 bg-[#1E1F22] ${
            !showFileList ? "w-10 cursor-pointer hover:bg-[#2B2D31]" : ""
          }`}
          style={showFileList ? { width: `${filesWidth}px` } : {}}
          onClick={() => !showFileList && setShowFileList(true)}
        >
          {!showFileList ? (
            /* --- VERTICAL TILED MODE (Closed) --- */
            <div className="flex flex-col items-center py-4 h-full gap-8">
              <ChevronRight className="w-4 h-4 text-zinc-500 mb-2" />
              <div 
                className="flex items-center gap-2" 
                style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
              >
                <span className="font-bold text-[11px] text-zinc-400 uppercase tracking-[0.2em]">
                  Files
                </span>
                <FileText className="w-3.5 h-3.5 text-zinc-500 rotate-90" />
              </div>
            </div>
          ) : (
            /* --- OPEN SIDEBAR CONTENT --- */
            <>
              {/* Sidebar Header */}
              <div
                className="px-4 py-3 border-b border-white/5 cursor-pointer flex items-center justify-between sticky top-0 z-10 bg-[#2B2D31]/50 backdrop-blur-md hover:bg-[#2B2D31] transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowFileList(false);
                }}
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-zinc-400" />
                  <span className="font-bold text-[10px] text-zinc-400 uppercase tracking-[0.15em]">
                    Files
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-md bg-[#2B2D31] text-zinc-500 font-medium ${jetbrainsMono.className}`}>
                    {prData.file_changes.length}
                  </span>
                </div>
                <ChevronLeft className="w-4 h-4 text-zinc-600" />
              </div>

              {/* File List */}
              <div className="overflow-y-auto h-[calc(100%-48px)] custom-scrollbar">
                {prData.file_changes.map((fileChange) => {
                  const fileIconData = getFileIcon(fileChange.file_path);
                  const isSelected = selectedFile === fileChange.file_path;
                  
                  return (
                    <button
                      key={fileChange.file_path}
                      onClick={() => setSelectedFile(fileChange.file_path)}
                      className={`w-full px-4 py-3 text-left transition-all border-b border-white/5 ${
                        isSelected
                          ? "bg-[#2B2D31] border-l-2 border-l-emerald-500 shadow-inner"
                          : "hover:bg-[#2B2D31]/40 border-l-2 border-l-transparent"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${fileIconData.color} ${jetbrainsMono.className} mt-0.5`}>
                          {fileIconData.icon}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className={`font-semibold truncate text-[13px] mb-0.5 ${isSelected ? "text-white" : "text-zinc-400"}`}>
                            {fileChange.file_path.split("/").pop()}
                          </p>
                          <p className={`text-[10px] truncate ${isSelected ? "text-zinc-500" : "text-zinc-600"} ${jetbrainsMono.className}`}>
                            {fileChange.file_path}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* CODE EDITOR */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#1E1E1E]">
          {selectedFile ? (
            <>
              {/* File Header */}
              <div className="px-4 py-2 border-b border-zinc-800 flex items-center justify-between flex-shrink-0 bg-[#1E1E1E]">
                <div className="flex items-center gap-2.5">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${getFileIcon(selectedFile).color} ${jetbrainsMono.className}`}>
                    {getFileIcon(selectedFile).icon}
                  </span>
                  <span className={`font-medium text-xs text-zinc-300 ${jetbrainsMono.className}`}>
                    {selectedFile}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-500 font-medium uppercase">
                    {getLanguageFromPath(selectedFile)}
                  </span>
                </div>
              </div>

              {/* Monaco Editor */}
              <div className="flex-1 min-h-0">
                <Editor
                  height="100%"
                  language={getLanguageFromPath(selectedFile)}
                  value={fileContents[selectedFile] || ""}
                  onChange={(value) => handleCodeChange(selectedFile, value)}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: true },
                    fontSize: 13,
                    lineNumbers: "on",
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: "on",
                    padding: { top: 16, bottom: 16 },
                    lineHeight: 20,
                    fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    fontLigatures: true,
                    readOnly: isSubmitting,
                    renderLineHighlight: "all",
                    cursorBlinking: "smooth",
                    smoothScrolling: true,
                    scrollbar: {
                      verticalScrollbarSize: 8,
                      horizontalScrollbarSize: 8,
                    },
                  }}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <FileCode className="w-8 h-8 text-zinc-600" />
                </div>
                <p className="font-medium text-sm text-zinc-400">
                  Select a file to start editing
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SUBMIT FOOTER */}
      <div className="px-4 py-3 border-t border-zinc-800 flex-shrink-0 bg-[#0A0A0A]">
        {submissionStatus === "idle" || submissionStatus === "complete" ? (
          <button
            onClick={handleSubmitCode}
            disabled={isSubmitting}
            className={`w-full px-6 py-2.5 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all text-sm ${
              isSubmitting
                ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                : "bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-600/20"
            }`}
          >
            <Play className="w-4 h-4" />
            <span>Run & Submit</span>
          </button>
        ) : (
          <div className={`w-full px-6 py-2.5 rounded-lg border flex items-center justify-center gap-3 ${
              submissionStatus === "submitting"
                ? "bg-blue-600/10 border-blue-600/20"
                : "bg-amber-600/10 border-amber-600/20"
            }`}
          >
            {submissionStatus === "submitting" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                <span className="font-medium text-blue-400 text-sm">
                  Submitting code...
                </span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 animate-pulse text-amber-400" />
                <span className="font-medium text-amber-400 text-sm">
                  Evaluating submission...
                </span>
              </>
            )}
          </div>
        )}
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0A0A0A;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #27272A;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #3F3F46;
        }
      `}</style>
    </div>
  );
}