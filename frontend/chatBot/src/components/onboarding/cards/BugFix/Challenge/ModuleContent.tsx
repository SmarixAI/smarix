"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneLight,
} from "react-syntax-highlighter/dist/esm/styles/prism";
import type { CodingQuestion } from "../../../../../../types/onboarding";
import React from "react";
import CodeEditor from "../../../utils/BugFix/CodeEditor";
import {
  BookOpen,
  Code2,
  Lightbulb,
  CheckCircle2,
  Clock,
  Maximize2,
  Minimize2,
} from "lucide-react";
import EvaluationModal from "../../../utils/BugFix/EvaluationModal";

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
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // Percentage
  const [isResizing, setIsResizing] = useState(false);
  const [challengeSolutionData, setChallengeSolutionData] = useState<any>(null);

  // Fetch challenge solution data from API
  React.useEffect(() => {
    const fetchSolutionData = async () => {
      try {
        // Use the first active repo if available
        const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
        const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';
        
        const response = await fetch(`/api/onboarding/bugFix/solutions${repoParam}`);
        if (response.ok) {
          const data = await response.json();
          setChallengeSolutionData(data);
        }
      } catch (error) {
        console.error('Error fetching challenge solution data:', error);
      }
    };

    fetchSolutionData();
  }, [activeRepos]);

  React.useEffect(() => {
    if (!challengeSolutionData) return;

    let prMatch = challenge.raw_response.match(/Issue\/PR\s*#?(\d+)/i);
    if (!prMatch) {
      prMatch = challenge.raw_response.match(/PR\s*#?(\d+)/i);
    }
    if (!prMatch) {
      prMatch = challenge.raw_response.match(/Issue\s*#?(\d+)/i);
    }
    if (!prMatch) {
      prMatch = challenge.raw_response.match(/pull request\s*#?(\d+)/i);
    }
    if (!prMatch) {
      prMatch = challenge.raw_response.match(/in\s+PR\s*#?(\d+)/i);
    }

    if (prMatch) {
      const prNumber = parseInt(prMatch[1]);
      const pr = challengeSolutionData.pull_requests?.find(
        (p: any) => p.pr_number === prNumber
      );
      if (pr) {
        setPrData(pr);
      }
    }
  }, [challenge, challengeSolutionData]);

  const challengeContent = challenge.raw_response.split("**Solution**")[0];
  const difficultyMatch = challenge.raw_response.match(/Difficulty:\s*(\w+)/i);
  const timeMatch = challenge.raw_response.match(/Estimated time:\s*([^\n]+)/i);

  const difficulty = difficultyMatch?.[1] || "Medium";
  const time = timeMatch?.[1] || "30-60 min";

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case "Easy":
        return "text-green-700 bg-green-50 border-green-200";
      case "Medium":
      case "Intermediate":
        return "text-yellow-700 bg-yellow-50 border-yellow-200";
      case "Hard":
        return "text-red-700 bg-red-50 border-red-200";
      default:
        return "text-gray-700 bg-gray-50 border-gray-200";
    }
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
      
      const container = document.querySelector('.challenge-container');
      if (!container) return;
      
      const rect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      
      // Constrain between 20% and 80%
      const constrainedWidth = Math.max(20, Math.min(80, newWidth));
      setLeftPanelWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  return (
    <>
      <div className="h-[calc(100vh-200px)] flex gap-0 challenge-container relative">
        {/* Left Panel - Challenge Description */}
        <div 
          className={`${isFullscreen ? "hidden" : ""} flex flex-col relative`}
          style={{ width: `${leftPanelWidth}%` }}
        >
          <div className="rounded-lg border border-gray-200 overflow-hidden shadow-sm h-full flex flex-col bg-white">
            {/* Header */}
            <div className="px-6 py-4 border-b flex-shrink-0 bg-white border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <h1 className="text-xl font-semibold text-gray-900">
                    Challenge {challenge.question_number}
                  </h1>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getDifficultyColor(
                      difficulty
                    )}`}
                  >
                    {difficulty}
                  </span>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{time}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <Code2 className="w-3.5 h-3.5" />
                    <span>{challenge.category}</span>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setActiveTab("description")}
                  className={`px-3 py-2 rounded-lg font-medium text-sm transition-all flex items-center space-x-2 ${
                    activeTab === "description"
                      ? "bg-gray-900 text-white"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Description</span>
                </button>

                <button
                  onClick={() => setActiveTab("hints")}
                  className={`px-3 py-2 rounded-lg font-medium text-sm transition-all flex items-center space-x-2 ${
                    activeTab === "hints"
                      ? "bg-gray-900 text-white"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`}
                >
                  <Lightbulb className="w-4 h-4" />
                  <span>Hints</span>
                </button>

                <button
                  onClick={() => setActiveTab("solution")}
                  className={`px-3 py-2 rounded-lg font-medium text-sm transition-all flex items-center space-x-2 ${
                    activeTab === "solution"
                      ? "bg-gray-900 text-white"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Solution</span>
                </button>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4 bg-gray-50">
              {activeTab === "description" && (
                <div className="prose max-w-none">
                  <ReactMarkdown
                    components={{
                      code(props) {
                        const { children, className, node, ref, ...rest } =
                          props;
                        const match = /language-(\w+)/.exec(className || "");
                        return match ? (
                          <div className="my-4 rounded-lg overflow-hidden border border-gray-200">
                            <div className="px-3 py-2 text-xs font-mono font-semibold flex items-center justify-between bg-gray-100 text-gray-700">
                              <span>{match[1]}</span>
                            </div>
                            <SyntaxHighlighter
                              PreTag="div"
                              language={match[1]}
                              style={oneLight}
                              customStyle={{
                                margin: 0,
                                padding: "1rem",
                                fontSize: "0.875rem",
                                lineHeight: "1.6",
                                background: "#f8fafc",
                              }}
                            >
                              {String(children).replace(/\n$/, "")}
                            </SyntaxHighlighter>
                          </div>
                        ) : (
                          <code className="px-1.5 py-0.5 rounded font-mono text-sm bg-gray-100 text-gray-800">
                            {children}
                          </code>
                        );
                      },
                      h1: ({ children }) => (
                        <h1 className="text-base font-semibold mb-3 mt-4 pb-2 border-b text-[#0E1B2E] border-[#0E1B2E]/10">
                          {children}
                        </h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="text-sm font-semibold mb-2 mt-4 text-[#0E1B2E]">
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="text-sm font-semibold mb-2 mt-3 text-[#0E1B2E]/90">
                          {children}
                        </h3>
                      ),
                      p: ({ children }) => (
                        <p className="mb-4 leading-relaxed text-sm text-gray-700">
                          {children}
                        </p>
                      ),
                      ul: ({ children }) => (
                        <ul className="mb-4 space-y-2">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="mb-4 space-y-2 list-decimal list-inside">
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => (
                        <li className="flex items-start text-sm leading-relaxed text-gray-700">
                          <span className="mr-2 mt-1 text-gray-600">
                            •
                          </span>
                          <span className="flex-1">{children}</span>
                        </li>
                      ),
                      strong: ({ children }) => (
                        <strong className="font-semibold text-gray-900">
                          {children}
                        </strong>
                      ),
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-4 pl-4 py-3 my-4 rounded-r italic border-gray-300 bg-gray-50 text-gray-700">
                          {children}
                        </blockquote>
                      ),
                      pre: ({ children }) => {
                        const childArray = React.Children.toArray(children);
                        const isCodeBlock = childArray.some((child) => {
                          if (React.isValidElement(child)) {
                            const props = child.props as { className?: string };
                            return props.className?.includes("language-");
                          }
                          return false;
                        });

                        if (isCodeBlock) {
                          return <>{children}</>;
                        }

                        return (
                          <pre className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                            {children}
                          </pre>
                        );
                      },
                    }}
                  >
                    {challengeContent}
                  </ReactMarkdown>
                </div>
              )}

              {activeTab === "hints" && (
                <div className="rounded-lg p-4 border bg-gray-50 border-gray-200">
                  <div className="flex items-start space-x-3">
                    <Lightbulb className="w-4 h-4 mt-0.5 text-[#0E1B2E]/70" />
                    <div>
                      <h4 className="text-sm font-semibold mb-2 text-[#0E1B2E]">
                        Helpful Tips
                      </h4>
                      <ul className="space-y-1.5 text-xs text-[#0E1B2E]/80">
                        <li className="flex items-start">
                          <span className="text-gray-600 mr-2">
                            →
                          </span>
                          <span>
                            Carefully read through the problem description and
                            understand the requirements
                          </span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-gray-600 mr-2">
                            →
                          </span>
                          <span>
                            Look at the file structure and identify which files
                            need to be modified
                          </span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-gray-600 mr-2">
                            →
                          </span>
                          <span>
                            Test your changes with different scenarios and edge
                            cases
                          </span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-gray-600 mr-2">
                            →
                          </span>
                          <span>
                            Make sure your code follows best practices and is
                            well-documented
                          </span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "solution" && (
                <div className="rounded-lg p-4 border bg-gray-50 border-gray-200">
                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="w-4 h-4 mt-0.5 text-[#0E1B2E]/70" />
                    <div>
                      <h4 className="text-sm font-semibold mb-2 text-[#0E1B2E]">
                        Solution Approach
                      </h4>
                      <p className="text-xs text-[#0E1B2E]/80">
                        Try to solve the challenge on your own first! The
                        solution will be revealed after you submit your code.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resizer */}
        {!isFullscreen && (
          <div
            onMouseDown={handleMouseDown}
            className={`w-1 cursor-col-resize hover:bg-gray-400 transition-colors flex-shrink-0 ${
              isResizing ? 'bg-gray-400' : 'bg-gray-300'
            }`}
            style={{ width: '4px' }}
          >
            <div className="w-full h-full" />
          </div>
        )}

        {/* Right Panel - Code Editor */}
        <div 
          className={`${isFullscreen ? "w-full" : ""} flex flex-col flex-1`}
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
