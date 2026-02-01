"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { CodingQuestion } from "../../../../../../types/onboarding";
import React from "react";
import CodeEditor from "../../../utils/BugFix/CodeEditor";
import {
  BookOpen,
  Code2,
  Lightbulb,
  CheckCircle2,
  Clock,
  Layout,
  Maximize2,
  Minimize2,
  AlertCircle,
} from "lucide-react";
import EvaluationModal from "../../../utils/BugFix/EvaluationModal";
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
});

interface ChallengeContentProps {
  challenge: CodingQuestion;
  activeRepos?: string[];
}

interface PullRequest {
  pr_number: number;
  file_changes: any[];
}

export default function ChallengeContent({
  challenge,
  activeRepos = [],
}: ChallengeContentProps) {
  const [prData, setPrData] = useState<PullRequest | null>(null);
  const [activeTab, setActiveTab] = useState<
    "description" | "hints" | "solution"
  >("description");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);
  const [challengeSolutionData, setChallengeSolutionData] = useState<any>(null);

  React.useEffect(() => {
    const fetchSolutionData = async () => {
      try {
        const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
        const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : "";

        const response = await fetch(
          `/api/onboarding/bugFix/solutions${repoParam}`
        );
        if (response.ok) {
          const data = await response.json();
          setChallengeSolutionData(data);
        }
      } catch (error) {
        console.error("Error fetching challenge solution data:", error);
      }
    };

    fetchSolutionData();
  }, [activeRepos]);

  React.useEffect(() => {
    if (!challengeSolutionData) return;
    // ... (PR Matching logic remains same) ...
    let prMatch = challenge.raw_response.match(/Issue\/PR\s*#?(\d+)/i);
    // ...
    if (prMatch) {
      const prNumber = parseInt(prMatch[1]);
      const pr = challengeSolutionData.pull_requests?.find(
        (p: any) => p.pr_number === prNumber
      );
      if (pr) setPrData(pr);
    }
  }, [challenge, challengeSolutionData]);

  const challengeContent = challenge.raw_response.split("**Solution**")[0];
  const difficultyMatch = challenge.raw_response.match(/Difficulty:\s*(\w+)/i);
  const timeMatch = challenge.raw_response.match(/Estimated time:\s*([^\n]+)/i);

  const difficulty = difficultyMatch?.[1] || "Medium";
  const time = timeMatch?.[1] || "30-60 min";

  const getDifficultyColor = (diff: string) => {
    const lower = diff.toLowerCase();
    if (lower === "easy")
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (lower === "hard") return "bg-rose-50 text-rose-700 border-rose-200";
    return "bg-amber-50 text-amber-700 border-amber-200";
  };

  const handleEvaluationComplete = (evalData: any) => {
    setEvaluationData(evalData);
    setShowEvaluationModal(true);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const container = document.querySelector(".challenge-container");
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftPanelWidth(Math.max(20, Math.min(80, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
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
  }, [isResizing]);

  return (
    <>
      <div className="h-[calc(100vh-200px)] flex gap-0 challenge-container relative rounded-2xl border-2 border-[#0E1B2E]/10 overflow-hidden bg-white shadow-xl shadow-[#0E1B2E]/5 animate-in fade-in slide-in-from-bottom-4 duration-500">
        {/* Left Panel - Challenge Description */}
        <div
          className={`${
            isFullscreen ? "hidden" : ""
          } flex flex-col relative bg-white`}
          style={{ width: `${leftPanelWidth}%` }}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-[#0E1B2E]/10 bg-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`${jetbrainsMono.className} text-xs font-bold text-[#0E1B2E]/40 bg-[#0E1B2E]/5 px-2 py-1 rounded`}
                >
                  #{challenge.question_number}
                </span>
                <h1
                  className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}
                >
                  Problem Statement
                </h1>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`${
                    inter.className
                  } px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wide border ${getDifficultyColor(
                    difficulty
                  )}`}
                >
                  {difficulty}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-medium text-[#0E1B2E]/60 mb-4">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>{time}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5" />
                <span>{challenge.category}</span>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex p-1 bg-[#0E1B2E]/5 rounded-lg border border-[#0E1B2E]/5">
              {[
                { id: "description", label: "Description", icon: BookOpen },
                { id: "hints", label: "Hints", icon: Lightbulb },
                { id: "solution", label: "Solution", icon: CheckCircle2 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-bold transition-all duration-200 ${
                    activeTab === tab.id
                      ? "bg-white text-[#0E1B2E] shadow-sm ring-1 ring-[#0E1B2E]/5"
                      : "text-[#0E1B2E]/60 hover:text-[#0E1B2E] hover:bg-[#0E1B2E]/5"
                  }`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto px-8 py-6 bg-slate-50/50">
            {activeTab === "description" && (
              <div className="prose prose-sm max-w-none prose-slate">
                <ReactMarkdown
                  components={{
                    code(props) {
                      const { children, className, node, ref, ...rest } = props;
                      const match = /language-(\w+)/.exec(className || "");
                      return match ? (
                        <div className="my-4 rounded-xl overflow-hidden border border-[#0E1B2E]/10 shadow-sm bg-white">
                          <div className="px-3 py-1.5 bg-[#0E1B2E]/5 border-b border-[#0E1B2E]/5 flex items-center justify-between">
                            <span
                              className={`${jetbrainsMono.className} text-[10px] font-bold text-[#0E1B2E]/60 uppercase`}
                            >
                              {match[1]}
                            </span>
                          </div>
                          <SyntaxHighlighter
                            PreTag="div"
                            language={match[1]}
                            style={oneLight}
                            customStyle={{
                              margin: 0,
                              padding: "1rem",
                              fontSize: "0.85rem",
                              background: "white",
                            }}
                          >
                            {String(children).replace(/\n$/, "")}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code
                          className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded text-[13px] bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/10`}
                        >
                          {children}
                        </code>
                      );
                    },
                    h1: ({ children }) => (
                      <h1
                        className={`${inter.className} text-lg font-bold mb-4 pb-2 border-b border-[#0E1B2E]/10 text-[#0E1B2E]`}
                      >
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2
                        className={`${inter.className} text-base font-bold mb-3 mt-6 text-[#0E1B2E]`}
                      >
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3
                        className={`${inter.className} text-sm font-bold mt-6 mb-3 text-[#0E1B2E]`}
                      >
                        {children}
                      </h3>
                    ),

                    h4: ({ children }) => (
                      <h4
                        className={`${inter.className} text-xs font-semibold mt-4 mb-2 text-[#0E1B2E]/90 uppercase tracking-wide`}
                      >
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p
                        className={`${inter.className} mb-4 leading-relaxed text-[#0E1B2E]/80`}
                      >
                        {children}
                      </p>
                    ),
                    li: ({ children }) => (
                      <li
                        className={`${inter.className} text-[#0E1B2E]/80 leading-relaxed`}
                      >
                        {children}
                      </li>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-500/30 bg-blue-50/50 pl-4 py-3 rounded-r my-4 text-[#0E1B2E]/70 italic">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {challengeContent}
                </ReactMarkdown>
              </div>
            )}

            {activeTab === "hints" && (
              <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                    <Lightbulb className="w-4 h-4 text-amber-600" />
                  </div>
                  <div>
                    <h4
                      className={`${inter.className} font-bold text-[#0E1B2E] mb-3`}
                    >
                      Helpful Hints
                    </h4>
                    <ul className="space-y-3">
                      {[
                        "Carefully read through the problem description and understand the requirements",
                        "Look at the file structure and identify which files need to be modified",
                        "Test your changes with different scenarios and edge cases",
                        "Make sure your code follows best practices and is well-documented",
                      ].map((hint, i) => (
                        <li
                          key={i}
                          className="flex gap-3 text-sm text-[#0E1B2E]/70"
                        >
                          <span className="text-amber-500 mt-0.5">•</span>
                          <span>{hint}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "solution" && (
              <div className="rounded-xl border border-[#0E1B2E]/10 bg-slate-50 p-8 text-center">
                <div className="w-12 h-12 rounded-xl bg-[#0E1B2E]/5 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-6 h-6 text-[#0E1B2E]/40" />
                </div>
                <h4
                  className={`${inter.className} font-bold text-[#0E1B2E] mb-2`}
                >
                  Solution Hidden
                </h4>
                <p
                  className={`${inter.className} text-sm text-[#0E1B2E]/60 max-w-sm mx-auto`}
                >
                  Try to solve the challenge on your own first! The solution
                  will be revealed after you attempt the challenge.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Resizer */}
        {!isFullscreen && (
          <div
            onMouseDown={handleMouseDown}
            className={`w-[1px] cursor-col-resize hover:bg-blue-500 transition-colors flex-shrink-0 relative z-10 group ${
              isResizing ? "bg-blue-500" : "bg-[#0E1B2E]/10"
            }`}
          >
            {/* Grip handle visual */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-8 bg-white border border-[#0E1B2E]/10 rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <div className="w-0.5 h-4 bg-[#0E1B2E]/20 rounded-full" />
            </div>
          </div>
        )}

        {/* Right Panel - Code Editor */}
        <div
          className={`${
            isFullscreen ? "w-full" : ""
          } flex flex-col flex-1 bg-[#1e1e1e]`} // Match editor bg
          style={!isFullscreen ? { width: `${100 - leftPanelWidth}%` } : {}}
        >
          <div className="h-full">
            <CodeEditor
              prData={prData || undefined}
              isFullscreen={isFullscreen}
              onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
              onEvaluationComplete={handleEvaluationComplete}
            />
          </div>
        </div>
      </div>

      {showEvaluationModal && (
        <EvaluationModal
          evaluationData={evaluationData}
          onClose={() => setShowEvaluationModal(false)}
        />
      )}
    </>
  );
}
