"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Code2,
  AlertCircle,
  ListChecks,
  Target,
  Lightbulb,
  Lock,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Inter, JetBrains_Mono } from "next/font/google";
import CodeEditor from "@/components/onboarding/utils/BugFix/CodeEditor";
import ContentSection from "@/components/onboarding/utils/BugFix/ContentSection";
import StepByStepSection from "@/components/onboarding/utils/BugFix/StepByStepSection";
import EvaluationModal from "@/components/onboarding/utils/BugFix/EvaluationModal";
import { parseTutorialContent } from "@/components/onboarding/utils/BugFix/contentParser";
import { useAuth } from "@/components/auth/AuthContext";

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

  const { user, loading: authLoading } = useAuth();
  // Ensure we have a string, fallback to empty if null
  const currentRepo =
    user?.activeRepos && user.activeRepos.length > 0 ? user.activeRepos[0] : "";

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);
  const [challengeSolutionData, setChallengeSolutionData] = useState<any>(null);

  const [activeTab, setActiveTab] = useState<"description" | "solution">(
    "description",
  );

  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [challengePrData, setChallengePrData] = useState<any>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // 1. Fetch Item Data
  useEffect(() => {
    const fetchData = async () => {
      if (authLoading) return;
      setLoading(true);
      setError(null);

      if (!currentRepo) {
        setLoading(false);
        return;
      }

      try {
        const repoParam = `?repo=${encodeURIComponent(currentRepo)}`;
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
        setData(result);
      } catch (err: any) {
        console.error("Fetch Details Error:", err);
        setError(err.message || "Failed to load details");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [type, id, currentRepo, authLoading]);

  // 2. Fetch Solutions
  useEffect(() => {
    const hasEmbeddedSolution = data?.solution?.files?.length > 0;
    if (
      type === "challenge" &&
      currentRepo &&
      !authLoading &&
      !hasEmbeddedSolution
    ) {
      const fetchSolutionData = async () => {
        try {
          const repoParam = `?repo=${encodeURIComponent(currentRepo)}`;
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
  }, [type, currentRepo, authLoading, data]);

  // --- PARSE CONTENT ---
  let parsedContent: any = {};
  if (data?.raw_response) {
    if (typeof data.raw_response === "object") {
      parsedContent = data.raw_response;
    } else if (typeof data.raw_response === "string") {
      try {
        let cleanJson = data.raw_response.trim();
        if (cleanJson.startsWith("```json")) {
          cleanJson = cleanJson.replace(/^```json/, "").replace(/```$/, "");
        } else if (cleanJson.startsWith("```")) {
          cleanJson = cleanJson.replace(/^```/, "").replace(/```$/, "");
        }
        parsedContent = JSON.parse(cleanJson);
      } catch (e) {
        parsedContent = { scenario: { context: data.raw_response } };
      }
    }
  }

  const challengeTitle =
    parsedContent.title || data?.title || `Challenge #${id}`;
  const challengeDifficulty =
    parsedContent.difficulty || data?.difficulty || "Medium";
  const challengeCategory =
    parsedContent.category || data?.category || "General";

  const scenarioContext = parsedContent.scenario?.context || "";
  const problemStatement = parsedContent.scenario?.problem_statement || "";
  const questionsList = parsedContent.questions || [];
  const keyConcepts = parsedContent.key_concepts || [];
  const modelAnswer = parsedContent.model_answer || {};

  const codeSnippetMatch =
    typeof data?.raw_response === "string"
      ? data.raw_response.match(
          /```(?:dart|java|javascript|typescript)?\s*([\s\S]*?)```/,
        )
      : null;
  const challengeCodeFallback = codeSnippetMatch ? codeSnippetMatch[1] : "";

  // 3. Match Challenge to PR Data
  useEffect(() => {
    if (type === "challenge" && data) {
      let computedFiles: any[] = [];
      let computedPrNumber = Number(data.pr_number || id);

      if (
        data.solution &&
        data.solution.files &&
        data.solution.files.length > 0
      ) {
        computedFiles = data.solution.files.map((f: any) => ({
          file_path: f.filename,
          change_type: "modified",
          before_code: f.before_code || "// Code unavailable",
          after_code: f.after_code || "",
          diff: f.diff || "",
          statistics: { lines_added: 0, lines_deleted: 0, total_changes: 0 },
        }));
      } else if (challengeSolutionData) {
        const list =
          challengeSolutionData.challenges ||
          challengeSolutionData.pull_requests ||
          [];
        const foundPr = list.find(
          (s: any) =>
            s.question_number?.toString() === id.toString() ||
            s.pr_number?.toString() === data.pr_number?.toString(),
        );

        if (foundPr) {
          computedPrNumber = Number(foundPr.pr_number);
          computedFiles = foundPr.file_changes || [];
        }
      }

      if (computedFiles.length === 0 && challengeCodeFallback) {
        computedFiles = [
          {
            file_path: "src/example.ts",
            change_type: "modified",
            before_code: challengeCodeFallback,
            after_code: challengeCodeFallback,
            diff: "",
            statistics: { lines_added: 0, lines_deleted: 0, total_changes: 0 },
          },
        ];
      }

      const validFiles = computedFiles.filter((f: any) => {
        const content = (f.before_code || "").trim();
        return (
          !content.includes("// Code unavailable") &&
          !content.includes("Code context unavailable")
        );
      });

      setChallengePrData({
        pr_number: computedPrNumber,
        file_changes: validFiles,
      });
    } else if (type === "challenge" && !data) {
      setChallengePrData(null);
    }
  }, [type, data, challengeSolutionData, id, challengeCodeFallback]);

  const getDifficultyColor = (diff: string) => {
    const lower = diff.toLowerCase();
    if (lower === "junior" || lower === "easy")
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (lower === "hard") return "bg-rose-50 text-rose-700 border-rose-200";
    return "bg-amber-50 text-amber-700 border-amber-200";
  };

  const handleEvaluationComplete = (evalData: any) => {
    setEvaluationData(evalData);
    setShowEvaluationModal(true);
    setIsSubmitted(true);
  };

  // --- Resizing ---
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const container = document.querySelector(".bugfix-detail-container");
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftPanelWidth(Math.max(20, Math.min(80, newWidth)));
    };
    const handleMouseUp = () => setIsResizing(false);
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

  const parsedTutorialData =
    type === "tutorial" && data?.raw_response
      ? parseTutorialContent(data.raw_response)
      : null;

  if (loading || authLoading) {
    return (
      <div
        className={`min-h-screen bg-[#FAFAFA] flex items-center justify-center ${inter.className}`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className={`text-slate-500 font-medium ${inter.className}`}>
            Loading content...
          </p>
        </div>
      </div>
    );
  }

  if (!currentRepo || error || !data) {
    return (
      <div
        className={`min-h-screen bg-[#FAFAFA] flex items-center justify-center ${inter.className}`}
      >
        <div className="flex flex-col items-center text-center p-8 bg-white rounded-2xl border-2 border-dashed border-slate-200">
          <AlertCircle className="w-12 h-12 text-slate-300 mb-4" />
          <h3 className={`text-lg font-bold text-slate-700 ${inter.className}`}>
            {error || "No Repository/Data Found"}
          </h3>
          <button
            onClick={() => router.back()}
            className={`mt-6 text-blue-600 font-medium hover:underline ${inter.className}`}
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-[#FAFAFA] ${inter.className}`}>
      <div className="h-screen w-screen flex gap-0 bugfix-detail-container relative overflow-hidden bg-white">
        {/* LEFT PANEL */}
        <div
          className={`flex flex-col relative bg-white overflow-hidden border-r border-[#0E1B2E]/10 ${type === "challenge" && isFullscreen ? "hidden" : ""}`}
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
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getDifficultyColor(challengeDifficulty)} ${inter.className}`}
                >
                  {challengeDifficulty.toLowerCase() === "junior"
                    ? "Easy"
                    : challengeDifficulty.toLowerCase() === "mid"
                      ? "Medium"
                      : challengeDifficulty}
                </span>
              </div>
            </div>

            <h1
              className={`text-lg font-bold text-[#0E1B2E] line-clamp-1 ${inter.className}`}
            >
              {challengeTitle}
            </h1>

            {type === "challenge" && (
              <div className="flex items-center gap-4 text-xs font-medium text-[#0E1B2E]/60 mt-3">
                <div className="flex items-center gap-1.5">
                  <Code2 className="w-3.5 h-3.5" />
                  <span className={inter.className}>{challengeCategory}</span>
                </div>
                <div className="flex gap-2 ml-auto">
                  {[
                    { id: "description", label: "Description", icon: BookOpen },
                    { id: "solution", label: "Solution", icon: CheckCircle2 },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${inter.className} ${activeTab === tab.id ? "bg-[#0E1B2E]/5 text-[#0E1B2E]" : "text-[#0E1B2E]/40 hover:text-[#0E1B2E]"}`}
                    >
                      <tab.icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto bg-slate-50/50 no-scrollbar">
            <div className="px-6 py-6 max-w-4xl mx-auto">
              {type === "challenge" && (
                <>
                  {activeTab === "description" && (
                    <div className="space-y-8">
                      {/* Scenario Section */}
                      {(scenarioContext || problemStatement) && (
                        <div className="space-y-4">
                          <div
                            className={`flex items-center gap-2 text-sm font-bold text-[#0E1B2E] uppercase tracking-wider ${inter.className}`}
                          >
                            <Target className="w-4 h-4 text-blue-600" />
                            Scenario
                          </div>
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                            {scenarioContext && (
                              <div>
                                <h4
                                  className={`text-xs font-bold text-slate-400 mb-1 uppercase ${inter.className}`}
                                >
                                  Context
                                </h4>
                                <p
                                  className={`text-sm text-slate-700 leading-relaxed ${inter.className}`}
                                >
                                  {scenarioContext}
                                </p>
                              </div>
                            )}
                            {problemStatement && (
                              <div>
                                <h4
                                  className={`text-xs font-bold text-slate-400 mb-1 uppercase ${inter.className}`}
                                >
                                  Problem Statement
                                </h4>
                                <p
                                  className={`text-sm text-slate-700 leading-relaxed font-medium ${inter.className}`}
                                >
                                  {problemStatement}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Questions Section */}
                      {questionsList.length > 0 && (
                        <div className="space-y-4">
                          <div
                            className={`flex items-center gap-2 text-sm font-bold text-[#0E1B2E] uppercase tracking-wider ${inter.className}`}
                          >
                            <ListChecks className="w-4 h-4 text-blue-600" />
                            Guiding Questions
                          </div>
                          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                            {questionsList.map((q: string, idx: number) => (
                              <div
                                key={idx}
                                className="p-4 border-b border-slate-100 last:border-0 flex gap-3"
                              >
                                <span
                                  className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-blue-50 text-blue-600 text-xs font-bold ${inter.className}`}
                                >
                                  {idx + 1}
                                </span>
                                <p
                                  className={`text-sm text-slate-700 leading-relaxed ${inter.className}`}
                                >
                                  {q}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Key Concepts */}
                      {keyConcepts.length > 0 && (
                        <div className="space-y-3">
                          <div
                            className={`flex items-center gap-2 text-sm font-bold text-[#0E1B2E] uppercase tracking-wider ${inter.className}`}
                          >
                            <Lightbulb className="w-4 h-4 text-amber-500" />
                            Key Concepts
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {keyConcepts.map((concept: string, idx: number) => (
                              <span
                                key={idx}
                                className={`px-3 py-1 rounded-full bg-amber-50 border border-amber-100 text-amber-700 text-xs font-bold shadow-sm ${inter.className}`}
                              >
                                {concept}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === "solution" && (
                    <div className="space-y-6">
                      {!isSubmitted ? (
                        // LOCKED STATE
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <Lock className="w-8 h-8 text-slate-400" />
                          </div>
                          <h3
                            className={`text-lg font-bold text-slate-700 mb-2 ${inter.className}`}
                          >
                            Solution Locked
                          </h3>
                          <p
                            className={`text-sm text-slate-500 max-w-sm mb-6 ${inter.className}`}
                          >
                            Submit your code attempt via the editor to unlock
                            the detailed solution, analysis, and best practices.
                          </p>
                          <div
                            className={`px-4 py-2 bg-slate-100 rounded-lg text-xs font-mono text-slate-500 border border-slate-200 ${inter.className}`}
                          >
                            Waiting for submission...
                          </div>
                        </div>
                      ) : (
                        // UNLOCKED STATE
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                          {/* Success Banner */}
                          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 flex items-start gap-3">
                            <ShieldCheck className="w-5 h-5 text-emerald-600 mt-0.5" />
                            <div>
                              <h4
                                className={`text-sm font-bold text-emerald-800 ${inter.className}`}
                              >
                                Solution Unlocked
                              </h4>
                              <p
                                className={`text-xs text-emerald-600 mt-1 ${inter.className}`}
                              >
                                Review the model answer below to compare with
                                your approach.
                              </p>
                            </div>
                          </div>

                          {/* Analysis & Solution */}
                          <div className="space-y-4">
                            <h3
                              className={`text-sm font-bold text-[#0E1B2E] uppercase tracking-wider flex items-center gap-2 ${inter.className}`}
                            >
                              <Target className="w-4 h-4 text-blue-600" />
                              Analysis
                            </h3>
                            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                              {modelAnswer.problem_analysis && (
                                <div className="p-5 border-b border-slate-100">
                                  <h4
                                    className={`text-xs font-bold text-slate-400 uppercase mb-2 ${inter.className}`}
                                  >
                                    Problem Analysis
                                  </h4>
                                  <p
                                    className={`text-sm text-slate-700 leading-relaxed ${inter.className}`}
                                  >
                                    {modelAnswer.problem_analysis}
                                  </p>
                                </div>
                              )}
                              {modelAnswer.solution_explanation && (
                                <div className="p-5">
                                  <h4
                                    className={`text-xs font-bold text-slate-400 uppercase mb-2 ${inter.className}`}
                                  >
                                    Solution Explanation
                                  </h4>
                                  <p
                                    className={`text-sm text-slate-700 leading-relaxed ${inter.className}`}
                                  >
                                    {modelAnswer.solution_explanation}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Trade-offs & Best Practices */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {modelAnswer.trade_offs && (
                              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                <h4
                                  className={`text-xs font-bold text-slate-400 uppercase mb-3 flex items-center gap-2 ${inter.className}`}
                                >
                                  <Zap className="w-3.5 h-3.5" /> Trade-offs
                                </h4>
                                <p
                                  className={`text-sm text-slate-700 leading-relaxed ${inter.className}`}
                                >
                                  {modelAnswer.trade_offs}
                                </p>
                              </div>
                            )}
                            {modelAnswer.best_practices && (
                              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                <h4
                                  className={`text-xs font-bold text-slate-400 uppercase mb-3 flex items-center gap-2 ${inter.className}`}
                                >
                                  <CheckCircle2 className="w-3.5 h-3.5" /> Best
                                  Practices
                                </h4>
                                <ul className="space-y-2">
                                  {modelAnswer.best_practices.map(
                                    (bp: string, i: number) => (
                                      <li
                                        key={i}
                                        className={`text-sm text-slate-700 flex items-start gap-2 ${inter.className}`}
                                      >
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                                        {bp}
                                      </li>
                                    ),
                                  )}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* TUTORIAL RENDER */}
              {type === "tutorial" && parsedTutorialData && (
                <div className="space-y-8">
                  {parsedTutorialData.overview && (
                    <ContentSection
                      title="Overview"
                      content={parsedTutorialData.overview}
                    />
                  )}
                  {parsedTutorialData.problemContext && (
                    <ContentSection
                      title="Problem Context"
                      content={parsedTutorialData.problemContext}
                    />
                  )}
                  {parsedTutorialData.keyTakeaways && (
                    <ContentSection
                      title="Key Takeaways"
                      content={parsedTutorialData.keyTakeaways}
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resizer */}
        {!isFullscreen && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
            className={`w-[4px] cursor-col-resize hover:bg-blue-500 transition-colors relative z-20 flex items-center justify-center group ${isResizing ? "bg-blue-500" : "bg-slate-200"}`}
          >
            <div className="w-1 h-8 bg-slate-400 rounded-full group-hover:bg-white" />
          </div>
        )}

        {/* RIGHT PANEL */}
        <div
          className={`flex flex-col overflow-hidden ${type === "challenge" ? "bg-[#1e1e1e]" : "bg-white"} ${isFullscreen ? "fixed inset-0 z-50 w-screen h-screen" : "relative flex-1"}`}
        >
          {type === "challenge" ? (
            <div className="h-full">
              {/* ✅ PASSED repoName prop here */}
              <CodeEditor
                prData={challengePrData || undefined}
                isFullscreen={isFullscreen}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onEvaluationComplete={handleEvaluationComplete}
                repoName={currentRepo}
              />
            </div>
          ) : parsedTutorialData ? (
            <div className="flex-1 px-8 py-6 bg-[#0E1B2E] no-scrollbar">
              <div className="max-w-4xl mx-auto space-y-8 rounded-full">
                {parsedTutorialData.steps.length > 0 && (
                  <StepByStepSection steps={parsedTutorialData.steps} />
                )}
                {parsedTutorialData.codeExplanation && (
                  <ContentSection
                    title="Code Explanation"
                    content={parsedTutorialData.codeExplanation}
                  />
                )}
              </div>
            </div>
          ) : (
            <div
              className={`flex items-center justify-center h-full text-slate-400 ${inter.className}`}
            >
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
