"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  Lightbulb,
  CheckCircle2,
  Clock,
  Code2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Inter, JetBrains_Mono } from "next/font/google";
import CodeEditor from "@/components/onboarding/utils/BugFix/CodeEditor";
import ContentSection from "@/components/onboarding/utils/BugFix/ContentSection";
import StepByStepSection from "@/components/onboarding/utils/BugFix/StepByStepSection";
import EvaluationModal from "@/components/onboarding/utils/BugFix/EvaluationModal";
import { parseTutorialContent } from "@/components/onboarding/utils/BugFix/contentParser";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export default function BugFixDetailPage() {
  const params = useParams();
  const router = useRouter();
  const type = params.type as string;
  const id = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);
  const [activeRepos, setActiveRepos] = useState<string[]>([]);
  const [challengeSolutionData, setChallengeSolutionData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<
    "description" | "hints" | "solution"
  >("description");
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [challengePrData, setChallengePrData] = useState<any>(null);

  // 1. Fetch Active Repos
  useEffect(() => {
    const fetchActiveRepos = async () => {
      try {
        const storedUser = localStorage.getItem("user");
        if (storedUser) {
          const user = JSON.parse(storedUser);
          let repos = user.active_repos || [];

          if (!repos || repos.length === 0) {
            const usersRes = await fetch("/api/users");
            if (usersRes.ok) {
              const usersData = await usersRes.json();
              const currentUser = usersData.users?.find(
                (u: any) =>
                  u.employeeId === user.employeeId ||
                  u.username === user.username,
              );
              if (currentUser?.active_repos) {
                repos = currentUser.active_repos;
              }
            }
          }
          setActiveRepos(repos);
        }
      } catch (error) {
        console.error("Error fetching active repos:", error);
      }
    };
    fetchActiveRepos();
  }, []);

  // 2. Fetch Item Data (Tutorial or Challenge)
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      // Guard: Wait for repos to be loaded to avoid 400 Bad Request
      if (activeRepos.length === 0) return;

      try {
        const repo = activeRepos[0];
        const repoParam = `?repo=${encodeURIComponent(repo)}`;

        // Use specific ID endpoints for both types
        // Matches structure: /api/onboarding/bugFix/challenges/[id]
        const endpoint =
          type === "tutorial"
            ? `/api/onboarding/bugFix/tutorials/${id}${repoParam}`
            : `/api/onboarding/bugFix/challenges/${id}${repoParam}`;

        const response = await fetch(endpoint);

        if (!response.ok) {
          if (response.status === 404)
            throw new Error(
              `${type === "tutorial" ? "Tutorial" : "Challenge"} not found`,
            );
          throw new Error("Failed to fetch data");
        }

        const result = await response.json();
        // Result is now the specific item object, not a list
        setData(result);
      } catch (err: any) {
        console.error("Fetch Details Error:", err);
        setError(err.message || "Failed to load details");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [type, id, activeRepos]);

  // 3. Fetch Solutions (Only for Challenges)
  useEffect(() => {
    if (type === "challenge" && activeRepos.length > 0) {
      const fetchSolutionData = async () => {
        try {
          const repo = activeRepos[0];
          const repoParam = `?repo=${encodeURIComponent(repo)}`;
          // Use 'bugFix/solutions' based on your provided file structure
          const response = await fetch(
            `/api/onboarding/bugFix/solutions${repoParam}`,
          );
          if (response.ok) {
            const solutionData = await response.json();
            setChallengeSolutionData(solutionData);
          }
        } catch (error) {
          console.error("Error fetching solutions:", error);
        }
      };
      fetchSolutionData();
    }
  }, [type, activeRepos]);

  // --- PARSE CHALLENGE CONTENT (Fix for empty fields) ---
  let challengeParsed: any = {};
  if (type === "challenge" && data) {
    try {
      // If raw_response is a JSON string, parse it. Otherwise use it as string.
      challengeParsed =
        typeof data.raw_response === "string" &&
        data.raw_response.trim().startsWith("{")
          ? JSON.parse(data.raw_response)
          : { problem: data.raw_response };
    } catch (e) {
      challengeParsed = { problem: data.raw_response };
    }
  }

  const challengeTitle =
    challengeParsed.title || data?.title || `Challenge #${id}`;
  const challengeDescription =
    challengeParsed.problem ||
    challengeParsed.description ||
    "No description available.";
  const challengeDifficulty =
    challengeParsed.difficulty || data?.difficulty || "Medium";
  const challengeTime = challengeParsed.estimated_time || "30-60 min";
  const challengeCategory =
    challengeParsed.category || data?.category || "General";

  // 4. Match Challenge to PR Data (Solution)
  useEffect(() => {
    if (type === "challenge" && data && challengeSolutionData) {
      // 1. Try matching by question_number (most reliable)
      // data is the specific challenge object now
      const sol = (challengeSolutionData.challenges || []).find(
        (s: any) => s.question_number?.toString() === id.toString(),
      );

      if (sol) {
        setChallengePrData({
          pr_number: sol.pr_number || id,
          file_changes: sol.file_changes || [],
        });
      } else {
        // 2. Fallback: Parse description for PR number
        const prMatch = challengeDescription.match(/Issue\/PR\s*#?(\d+)/i);
        if (prMatch) {
          const prNumber = parseInt(prMatch[1]);
          // If we can't find files, we might just mock the PR ID so the editor opens
          setChallengePrData({
            pr_number: prNumber,
            file_changes: [],
          });
        }
      }
    } else if (type === "challenge" && !data) {
      setChallengePrData(null);
    }
  }, [type, data, challengeSolutionData, id, challengeDescription]);

  // --- UI HELPERS ---
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

  // --- RESIZING LOGIC ---
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const container = document.querySelector(".bugfix-detail-container");
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

  // Parse Tutorial Content (Markdown)
  const parsedTutorial =
    type === "tutorial" && data?.raw_response
      ? parseTutorialContent(data.raw_response)
      : null;

  // Prepare PR Data for Tutorial Mode
  const tutorialPrData =
    type === "tutorial" && data?.file_changes
      ? {
          pr_number: data.pr_number || data.tutorial_number,
          file_changes: data.file_changes,
        }
      : null;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || "Data not found"}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
          >
            <ArrowLeft className="w-4 h-4" /> Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* Container */}
      <div className="h-screen w-screen flex gap-0 bugfix-detail-container relative overflow-hidden bg-white">
        {/* LEFT PANEL: Content (Tutorial Steps or Challenge Description) */}
        <div
          className={`flex flex-col relative bg-white overflow-hidden border-r border-[#0E1B2E]/10 ${
            type === "challenge" && isFullscreen ? "hidden" : ""
          }`}
          style={{ width: `${leftPanelWidth}%` }}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-[#0E1B2E]/10 bg-white flex-shrink-0">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => router.back()}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2">
                <span
                  className={`${jetbrainsMono.className} text-xs font-bold text-[#0E1B2E]/40 bg-[#0E1B2E]/5 px-2 py-1 rounded`}
                >
                  {type === "tutorial" ? `Module ${id}` : `Challenge ${id}`}
                </span>
                <span
                  className={`${inter.className} px-2 py-0.5 rounded text-[10px] font-bold border ${getDifficultyColor(challengeDifficulty || data?.difficulty || "Medium")}`}
                >
                  {challengeDifficulty || data?.difficulty || "Medium"}
                </span>
              </div>
            </div>

            <h1
              className={`${inter.className} text-lg font-bold text-[#0E1B2E] line-clamp-1`}
            >
              {type === "challenge"
                ? challengeTitle
                : data.pr_title || "Tutorial"}
            </h1>

            {/* Challenge Metadata */}
            {type === "challenge" && (
              <div className="flex items-center gap-4 text-xs font-medium text-[#0E1B2E]/60 mt-3">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{challengeTime}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Code2 className="w-3.5 h-3.5" />
                  <span>{challengeCategory}</span>
                </div>
              </div>
            )}

            {/* Challenge Tabs */}
            {type === "challenge" && (
              <div className="flex p-1 bg-[#0E1B2E]/5 rounded-lg border border-[#0E1B2E]/5 mt-4">
                {[
                  { id: "description", label: "Description", icon: BookOpen },
                  { id: "hints", label: "Hints", icon: Lightbulb },
                  { id: "solution", label: "Solution", icon: CheckCircle2 },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-bold transition-all ${
                      activeTab === tab.id
                        ? "bg-white text-[#0E1B2E] shadow-sm ring-1 ring-[#0E1B2E]/5"
                        : "text-[#0E1B2E]/60 hover:text-[#0E1B2E] hover:bg-[#0E1B2E]/5"
                    }`}
                  >
                    <tab.icon className="w-3.5 h-3.5" />
                    {tab.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Scrollable Body */}
          <div className="flex-1 overflow-y-auto bg-slate-50/50">
            <div className="px-6 py-6 max-w-4xl mx-auto">
              {/* CHALLENGE CONTENT */}
              {type === "challenge" && (
                <>
                  {activeTab === "description" && (
                    <div className="prose prose-sm max-w-none prose-slate">
                      <ReactMarkdown
                        components={{
                          code({ children, className }) {
                            const match = /language-(\w+)/.exec(
                              className || "",
                            );
                            return match ? (
                              <div className="my-4 rounded-xl overflow-hidden border border-[#0E1B2E]/10 bg-white shadow-sm">
                                <div className="px-3 py-1.5 bg-[#0E1B2E]/5 border-b text-xs font-bold uppercase text-[#0E1B2E]/60">
                                  {match[1]}
                                </div>
                                <SyntaxHighlighter
                                  PreTag="div"
                                  language={match[1]}
                                  style={oneLight}
                                  customStyle={{
                                    margin: 0,
                                    padding: "1rem",
                                    fontSize: "0.85rem",
                                  }}
                                >
                                  {String(children).replace(/\n$/, "")}
                                </SyntaxHighlighter>
                              </div>
                            ) : (
                              <code
                                className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 text-sm text-[#0E1B2E]`}
                              >
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {challengeDescription}
                      </ReactMarkdown>
                    </div>
                  )}

                  {activeTab === "hints" && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-6">
                      <h4
                        className={`${inter.className} font-bold mb-3 text-[#0E1B2E] flex items-center gap-2`}
                      >
                        <Lightbulb className="w-4 h-4 text-amber-600" /> Helpful
                        Hints
                      </h4>
                      <ul className="space-y-2 text-sm text-[#0E1B2E]/80 list-disc ml-5">
                        <li>
                          Analyze the requirements carefully before coding.
                        </li>
                        <li>
                          Check if any specific file names or function
                          signatures are required.
                        </li>
                        <li>Look for existing patterns in the codebase.</li>
                      </ul>
                    </div>
                  )}

                  {activeTab === "solution" && (
                    <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
                      <CheckCircle2 className="w-8 h-8 mx-auto mb-3 text-slate-300" />
                      <p className="text-sm text-slate-500 font-medium">
                        The solution will be revealed after you submit your
                        attempt.
                      </p>
                    </div>
                  )}
                </>
              )}

              {/* TUTORIAL CONTENT */}
              {type === "tutorial" && parsedTutorial && (
                <div className="space-y-8">
                  {parsedTutorial.overview && (
                    <ContentSection
                      title="Overview"
                      content={parsedTutorial.overview}
                    />
                  )}
                  {parsedTutorial.problemContext && (
                    <ContentSection
                      title="Problem Context"
                      content={parsedTutorial.problemContext}
                    />
                  )}
                  {parsedTutorial.keyTakeaways && (
                    <ContentSection
                      title="Key Takeaways"
                      content={parsedTutorial.keyTakeaways}
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resizer Handle */}
        {!isFullscreen && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
            className={`w-[4px] cursor-col-resize hover:bg-blue-500 transition-colors relative z-20 flex items-center justify-center group ${
              isResizing ? "bg-blue-500" : "bg-slate-200"
            }`}
          >
            <div className="w-1 h-8 bg-slate-400 rounded-full group-hover:bg-white" />
          </div>
        )}

        {/* RIGHT PANEL: Code Editor / Steps */}
        <div
          className={`flex flex-col overflow-hidden ${
            type === "challenge" ? "bg-[#1e1e1e]" : "bg-white"
          } ${
            isFullscreen
              ? "fixed inset-0 z-50 w-screen h-screen"
              : "relative flex-1"
          }`}
        >
          {type === "challenge" ? (
            <div className="h-full">
              <CodeEditor
                prData={challengePrData || undefined}
                isFullscreen={isFullscreen}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onEvaluationComplete={handleEvaluationComplete}
              />
            </div>
          ) : parsedTutorial ? (
            <div className="flex-1 overflow-y-auto px-8 py-6 bg-slate-50">
              <div className="max-w-4xl mx-auto space-y-8">
                {parsedTutorial.steps.length > 0 && (
                  <StepByStepSection steps={parsedTutorial.steps} />
                )}
                {parsedTutorial.codeExplanation && (
                  <ContentSection
                    title="Code Explanation"
                    content={parsedTutorial.codeExplanation}
                  />
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              <p>No code content available</p>
            </div>
          )}
        </div>
      </div>

      {showEvaluationModal && (
        <EvaluationModal
          evaluationData={evaluationData}
          onClose={() => setShowEvaluationModal(false)}
        />
      )}
    </div>
  );
}
