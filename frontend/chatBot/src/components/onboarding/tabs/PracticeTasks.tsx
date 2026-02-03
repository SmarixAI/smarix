"use client";

import { useEffect, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Shield,
  Lightbulb,
  AlertTriangle,
  Target,
  AlertCircle,
  ChevronDown,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Inter, JetBrains_Mono } from "next/font/google";
// ✅ 1. Import Auth Context
import { useAuth } from "@/components/auth/AuthContext";

interface PracticeTasksProps {
  tasks?: any[];
  openTask?: number | null;
  onSelectTask?: (n: number | null) => void;
  employeeId?: string | null;
  activeRepos?: string[];
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export default function PracticeTasks({
  tasks,
  openTask,
  onSelectTask,
  employeeId,
  activeRepos: propActiveRepos = [], // Rename to avoid conflict
  onUpdateProgress,
}: PracticeTasksProps) {
  // ✅ 2. Get User from Context
  const { user } = useAuth();

  // ✅ 3. Merge Prop with Auth Context (The Fix)
  // This ensures we have a repo even if the parent component forgot to pass it
  const activeRepos =
    propActiveRepos.length > 0 ? propActiveRepos : user?.activeRepos || [];

  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [missingRepo, setMissingRepo] = useState(false);

  const [practicedMap, setPracticedMap] = useState<Record<number, boolean>>({});
  const [expandedCode, setExpandedCode] = useState<Record<string, boolean>>({});
  const [activeStepMap, setActiveStepMap] = useState<Record<number, number>>(
    {},
  );

  useEffect(() => {
    if (openTask != null && activeStepMap[openTask] === undefined) {
      setActiveStepMap((p) => ({ ...p, [openTask]: 0 }));
    }
  }, [openTask]);

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      setError(null);
      setMissingRepo(false);

      // 1. Check if tasks passed via props have the content we need
      if (tasks && tasks.length > 0) {
        const hasFullContent = tasks.some(
          (task: any) =>
            task.steps && Array.isArray(task.steps) && task.steps.length > 0,
        );

        if (hasFullContent) {
          setData({ questions: tasks });
          setLoading(false);
          return;
        }
      }

      // 2. Standalone fetch Logic
      const repo = activeRepos && activeRepos.length > 0 ? activeRepos[0] : "";

      // Strict Guard Clause
      if (!repo) {
        console.warn(
          "PracticeTasks: No active repository assigned (Context or Props).",
        );
        setMissingRepo(true);
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `/api/onboarding/practice/practice1?repo=${encodeURIComponent(repo)}`,
        );

        if (response.ok) {
          const json = await response.json();
          let fetchedTasks = json.questions || json.tasks || [];

          // Merge with props if available
          if (tasks && tasks.length > 0) {
            fetchedTasks = fetchedTasks.map((t: any) => {
              const propTask = tasks.find(
                (pt: any) => pt.question_number === t.question_number,
              );
              return propTask ? { ...t, ...propTask } : t;
            });
          }

          setData({ questions: fetchedTasks });
        } else {
          setError("Failed to load practice tasks");
        }
      } catch (e) {
        console.error("Practice fetch error", e);
        setError("Failed to load practice tasks");
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [tasks, activeRepos]); // ✅ Depends on the derived activeRepos

  useEffect(() => {
    try {
      const raw = localStorage.getItem("onboard_practice_progress");
      if (raw) setPracticedMap(JSON.parse(raw));
    } catch {}
  }, []);

  const toggleCodeView = (taskNum: number, stepNum: number) => {
    const key = `${taskNum}-${stepNum}`;
    setExpandedCode((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const markTaskComplete = async (taskNum: number) => {
    const updated = { ...practicedMap, [taskNum]: true };
    setPracticedMap(updated);
    localStorage.setItem("onboard_practice_progress", JSON.stringify(updated));

    // Send to Backend
    if (employeeId && activeRepos.length > 0) {
      const repo = activeRepos[0];
      try {
        await fetch("/api/onboarding/progress", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            employeeId,
            section: "practice",
            itemId: `practice1`,
            updates: {
              status: "in-progress",
              progress: Math.round(
                (Object.keys(updated).length / (data?.questions?.length || 1)) *
                  100,
              ),
              completedTasks: Object.keys(updated).map(Number),
            },
            repo: repo,
          }),
        });

        if (onUpdateProgress) {
          onUpdateProgress("practice", `task-${taskNum}`, { completed: true });
        }
      } catch (error) {
        console.error("Failed to save practice progress", error);
      }
    }
  };

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p
            className={`${inter.className} text-sm text-slate-600 font-medium`}
          >
            Loading practice tasks…
          </p>
        </div>
      </div>
    );
  }

  // Missing Repo UI
  if (missingRepo) {
    return (
      <div className="p-12 text-center min-h-[300px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center mb-4 border border-amber-100">
          <AlertCircle className="w-8 h-8 text-amber-500" />
        </div>
        <h3 className={`${inter.className} text-lg font-bold text-slate-800`}>
          No Repository Assigned
        </h3>
        <p
          className={`${inter.className} text-sm text-slate-500 mt-2 max-w-xs leading-relaxed`}
        >
          Practice tasks are tied to your assigned repository. Please ask your
          manager to assign one.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`${inter.className} p-4 text-red-600 text-center bg-red-50 rounded-xl border border-red-200 m-4`}
      >
        {error}
      </div>
    );
  }

  if (!data || !data.questions || data.questions.length === 0) {
    return (
      <div className="p-4 text-center min-h-[300px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
          <Shield className="w-8 h-8 text-slate-400" />
        </div>
        <p
          className={`${inter.className} text-lg font-semibold text-slate-700 mb-2`}
        >
          No practice tasks available
        </p>
      </div>
    );
  }

  const activeTask =
    openTask != null
      ? data.questions.find(
          (t: any) => Number(t.question_number) === Number(openTask),
        )
      : null;

  return (
    <div className="w-auto pt-0 pl-4 pr-4 pb-4 relative">
      <div className="relative z-10 space-y-5">
        {!activeTask && (
          <div className="p-12 text-center rounded-2xl border-2 border-slate-200 bg-white/60">
            <p className={`${inter.className} text-slate-600 font-semibold`}>
              Select a task from the sidebar
            </p>
          </div>
        )}

        {activeTask &&
          (() => {
            const task = activeTask;
            const isCompleted = practicedMap[task.question_number];
            const idx = activeStepMap[task.question_number] ?? 0;
            const total = task.steps?.length || 1;
            const step = task.steps?.[idx];
            const key = `${task.question_number}-${step?.step_number || 1}`;

            return (
              <div
                key={task.question_number}
                className="space-y-5 lg:space-y-6"
              >
                {/* TASK OVERVIEW */}
                <div className="rounded-2xl border-2 border-slate-200 p-6 bg-white/70 backdrop-blur-sm shadow-md">
                  <div className="flex items-start justify-between mb-3">
                    <h3
                      className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}
                    >
                      {task.title || `Task #${task.question_number}`}
                    </h3>

                    {isCompleted && (
                      <div className="px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 bg-green-50 text-green-700 border-2 border-green-200">
                        <Check className="w-4 h-4" />
                        Completed
                      </div>
                    )}
                  </div>

                  <p
                    className={`${inter.className} text-[15px] leading-relaxed text-slate-700`}
                  >
                    {task.question_description ||
                      task.description ||
                      "Follow the steps below to complete this task."}
                  </p>
                </div>

                {/* STEPS */}
                {/* STEPS */}
                {task.steps && task.steps.length > 0 ? (
                  <div
                    className="
                      rounded-2xl border-2 border-slate-200 
                      bg-white/70 backdrop-blur-sm 
                      shadow-lg 
                      max-h-[70vh]   
                      w-full     
                      flex flex-col       
                      overflow-hidden
                    "
                  >
                    {/* STEP HEADER (static inside card) */}
                    <div className="px-6 py-5 border-b-2 bg-gradient-to-r from-slate-50 to-blue-50/30">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-[#0E1B2E] to-blue-900 text-white">
                            <span
                              className={`${jetbrainsMono.className} font-bold text-xl`}
                            >
                              {idx + 1}
                            </span>
                          </div>

                          <div>
                            <p className="text-sm font-semibold">
                              Step {idx + 1} of {total}
                            </p>
                            <p className="text-xs text-slate-600">
                              {step?.step_title || step?.title}
                            </p>
                          </div>
                        </div>

                        <span className="text-sm font-bold px-4 py-2 rounded-xl bg-blue-50 text-blue-700 border">
                          {Math.round(((idx + 1) / total) * 100)}%
                        </span>
                      </div>

                      <div className="flex gap-2">
                        {Array.from({ length: total }).map((_, i) => (
                          <div
                            key={i}
                            className={`h-2 flex-1 rounded-full ${
                              i <= idx
                                ? "bg-gradient-to-r from-[#0E1B2E] to-blue-600"
                                : "bg-slate-200"
                            }`}
                          />
                        ))}
                      </div>
                    </div>

                    {/* STEP CONTENT (scrollable) */}
                    <div
                      className="
                        px-6 py-6 space-y-5 
                        overflow-y-auto 
                      "
                    >
                      <div className="rounded-xl border-2 border-blue-200 p-5 bg-blue-50/40">
                        <h4 className="text-sm font-bold mb-3 flex items-center gap-2">
                          <Target className="w-4 h-4 text-blue-600" />
                          What to implement
                        </h4>
                        <div className="prose prose-sm max-w-none text-slate-700">
                          <ReactMarkdown>
                            {(
                              step?.what_to_do ||
                              step?.description ||
                              step?.implementation_details ||
                              "No details available."
                            ).replace(/^:\s*/, "")}
                          </ReactMarkdown>
                        </div>
                      </div>

                      {step?.tips && step.tips.length > 0 && (
                        <div className="rounded-xl border-2 border-yellow-200 p-5 bg-yellow-50/40">
                          <h4 className="text-sm font-bold mb-3 flex items-center gap-2 text-yellow-700">
                            <Lightbulb className="w-4 h-4" />
                            Tips
                          </h4>
                          <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700">
                            {step.tips.map((tip: string, i: number) => (
                              <li key={i}>{tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* CODE */}
                      <div
                        className="rounded-xl border-2 cursor-pointer overflow-hidden"
                        onClick={() =>
                          toggleCodeView(
                            task.question_number,
                            step?.step_number,
                          )
                        }
                      >
                        <div className="px-5 py-4 border-b flex items-center justify-between">
                          <span className="font-bold">
                            {expandedCode[key]
                              ? "Solution Code"
                              : "View Solution Code"}
                          </span>
                          <ChevronRight
                            className={`transition-transform ${
                              expandedCode[key] ? "rotate-90" : ""
                            }`}
                          />
                        </div>

                        {expandedCode[key] &&
                          (step?.code_snippet || step?.code) && (
                            <div className="bg-[#282c34] p-5">
                              <SyntaxHighlighter
                                language="java"
                                style={oneDark}
                                showLineNumbers
                              >
                                {step.code_snippet || step.code}
                              </SyntaxHighlighter>
                            </div>
                          )}
                      </div>
                    </div>

                    {/* NAVIGATION (static at bottom of card) */}
                    <div className="px-6 py-5 border-t flex justify-between bg-white/80">
                      <button
                        disabled={idx === 0}
                        onClick={() =>
                          setActiveStepMap((p) => ({
                            ...p,
                            [task.question_number]: Math.max(0, idx - 1),
                          }))
                        }
                        className="px-5 py-2.5 rounded-xl bg-slate-100 disabled:opacity-40"
                      >
                        <ChevronLeft className="inline w-4 h-4 mr-1" />
                        Previous
                      </button>

                      {idx === total - 1 ? (
                        <button
                          onClick={() => markTaskComplete(task.question_number)}
                          className="px-6 py-2.5 rounded-xl bg-green-600 text-white"
                        >
                          Mark Complete
                        </button>
                      ) : (
                        <button
                          onClick={() =>
                            setActiveStepMap((p) => ({
                              ...p,
                              [task.question_number]: idx + 1,
                            }))
                          }
                          className="px-6 py-2.5 rounded-xl bg-blue-900 text-white"
                        >
                          Next
                          <ChevronRight className="inline w-4 h-4 ml-1" />
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border-2 border-slate-200 p-12 text-center">
                    No steps available
                  </div>
                )}
              </div>
            );
          })()}
      </div>
    </div>
  );
}
