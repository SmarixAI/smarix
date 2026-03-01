"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import Editor, { OnMount } from "@monaco-editor/react";
import * as monaco from "monaco-editor";

interface Props {
  content: string;
  fileName?: string;
}

export default function CodeViewer({ content, fileName }: Props) {
  const [copied, setCopied] = useState(false);
  const [search, setSearch] = useState("");
  const [matchCount, setMatchCount] = useState(0);
  const [cursorPosition, setCursorPosition] = useState({
    line: 1,
    column: 1,
  });

  const editorRef =
    useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const decorationsRef = useRef<string[]>([]);

  // 🔥 Detect language
  const language = useMemo(() => {
    if (!fileName) return "plaintext";
    const ext = fileName.split(".").pop()?.toLowerCase();

    const map: Record<string, string> = {
      js: "javascript",
      ts: "typescript",
      jsx: "javascript",
      tsx: "typescript",
      py: "python",
      java: "java",
      cpp: "cpp",
      c: "c",
      go: "go",
      rb: "ruby",
      php: "php",
      json: "json",
      html: "html",
      css: "css",
      dart: "dart",
      kt: "kotlin",
      swift: "swift",
    };

    return map[ext || ""] || "plaintext";
  }, [fileName]);

  // 🔥 Copy
  async function handleCopy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  // 🔥 Highlight search matches
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;

    const model = editor.getModel();
    if (!model) return;

    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current,
      []
    );

    if (!search) {
      setMatchCount(0);
      return;
    }

    const matches = model.findMatches(
      search,
      true,
      false,
      false,
      null,
      true
    );

    setMatchCount(matches.length);

    const newDecorations = matches.map((match) => ({
      range: match.range,
      options: {
        inlineClassName: "bg-yellow-400/40 rounded-sm",
      },
    }));

    decorationsRef.current = editor.deltaDecorations(
      [],
      newDecorations
    );

    if (matches.length > 0) {
      editor.revealRangeInCenter(matches[0].range);
    }
  }, [search, content]);

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor;

    editor.onDidChangeCursorPosition((e) => {
      setCursorPosition({
        line: e.position.lineNumber,
        column: e.position.column,
      });
    });
  };

  if (!content) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1E1E1E] text-gray-500">
        Select a file to view content
      </div>
    );
  }

  return (
    <div className="relative flex-1 bg-[#1E1E1E]">

      {/* 🔥 Floating Controls */}
      <div className="absolute top-4 right-4 z-20 flex flex-col items-end gap-2">

        {/* Search + Copy Row */}
        <div className="flex items-center gap-2 bg-[#111827]/90 backdrop-blur-md px-3 py-2 rounded-lg border border-[#1F2937] shadow-lg">

          <input
            type="text"
            placeholder="Find..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-[#1F2937] text-xs px-2 py-1 rounded-md text-gray-200 outline-none"
          />

          {search && (
            <span className="text-yellow-400 text-xs">
              {matchCount}
            </span>
          )}

          {search && (
            <button
              onClick={() => setSearch("")}
              className="text-xs text-gray-400 hover:text-white"
            >
              ✕
            </button>
          )}

          <button
            onClick={handleCopy}
            className="bg-[#2A2D2E] hover:bg-[#3A3D3E]
                       text-xs px-3 py-1 rounded-lg
                       text-gray-300 transition"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>

        {/* Code Locator */}
        <div className="text-xs text-gray-400 bg-[#111827]/90 backdrop-blur-md px-3 py-1 rounded-md border border-[#1F2937] shadow">
          Ln {cursorPosition.line}, Col {cursorPosition.column}
        </div>

      </div>

      {/* 🔥 Monaco Editor */}
      <Editor
        height="100%"
        language={language}
        value={content}
        theme="vs-dark"
        onMount={handleEditorMount}
        options={{
          readOnly: true,
          minimap: { enabled: true },
          fontSize: 14,
          scrollBeyondLastLine: false,
          folding: true,
          foldingHighlight: true,
          showFoldingControls: "always",
          lineNumbers: "on",
          wordWrap: "on",
          automaticLayout: true,
        }}
      />

    </div>
  );
}