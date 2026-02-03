"use client";

import { useState, useEffect } from "react";
import {
  BookOpen,
  Users,
  Sparkles,
  ListTree,
  ChevronRight,
  Bug,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
} from "lucide-react";
import { Inter } from "next/font/google";
import { useAuth } from "@/components/auth/AuthContext"; // ✅ Import Auth

interface SidebarProps {
  completedModules: number;
  totalModules: number;
  activeTab: string;
  practiceTasks?: any[];
  selectedPracticeTask?: number | null;
  onSelectPracticeTask?: (key: number) => void;
  tutorialsCount?: number;
  challengesCount?: number;
  completedTutorials?: number;
  completedChallenges?: number;
  activeMode?: "tutorials" | "challenges";
  onSwitchMode?: (mode: "tutorials" | "challenges") => void;
}

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export default function Sidebar({
  completedModules,
  totalModules,
  activeTab,
  practiceTasks: propTasks = [], // Rename prop
  selectedPracticeTask = null,
  onSelectPracticeTask,
  tutorialsCount,
  challengesCount,
  completedTutorials = 0,
  completedChallenges = 0,
  activeMode,
  onSwitchMode,
}: SidebarProps) {
  const { user } = useAuth();

  // ✅ Local state for fetched tasks if props are missing
  const [fetchedTasks, setFetchedTasks] = useState<any[]>([]);
  const [completionMap, setCompletionMap] = useState<Record<number, boolean>>(
    {},
  );
  const [tasksExpanded, setTasksExpanded] = useState<boolean>(true);

  // Combine props with fetched data
  const practiceTasks = propTasks.length > 0 ? propTasks : fetchedTasks;

  useEffect(() => {
    try {
      const raw = localStorage.getItem("onboard_practice_progress");
      if (raw) setCompletionMap(JSON.parse(raw));
    } catch {}
  }, []);

  // ✅ NEW: Fetch tasks if sidebar is active and no props provided
  useEffect(() => {
    const loadSidebarTasks = async () => {
      if (
        activeTab === "practice" &&
        propTasks.length === 0 &&
        user?.activeRepos &&
        user.activeRepos.length > 0
      ) {
        try {
          const repo = user.activeRepos[0];
          const res = await fetch(
            `/api/onboarding/practice/practice1?repo=${encodeURIComponent(repo)}`,
          );
          if (res.ok) {
            const json = await res.json();
            setFetchedTasks(json.questions || json.tasks || []);
          }
        } catch (e) {
          console.error("Sidebar fetch error:", e);
        }
      }
    };
    loadSidebarTasks();
  }, [activeTab, propTasks.length, user]);

  const getDifficultyColor = (diff: string) => {
    switch (diff?.toLowerCase()) {
      case "easy":
        return "bg-emerald-50 text-emerald-700 border-emerald-100";
      case "intermediate":
        return "bg-amber-50 text-amber-700 border-amber-100";
      case "hard":
        return "bg-rose-50 text-rose-700 border-rose-100";
      default:
        return "bg-slate-50 text-slate-600 border-slate-100";
    }
  };

  if (activeTab === "practice") {
    const completedTasks = Object.keys(completionMap).length;
    const totalTasks = practiceTasks?.length || 0;
    const completionPercent =
      totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

    return (
      <aside
        className="flex-shrink-0 flex flex-col bg-white/70 rounded-2xl border-2 border-slate-200/60 shadow-lg shadow-slate-200/30 overflow-hidden"
        style={{ height: "calc(100vh - 200px)" }}
      >
        {/* HEADER */}
        <div className="p-5 border-b-2 border-slate-200/60 flex-shrink-0 bg-gradient-to-br from-white to-blue-50/30">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3
                className={`${inter.className} font-bold text-base text-[#0E1B2E]`}
              >
                Practice Tasks
              </h3>
              <p
                className={`${inter.className} text-xs text-slate-600 font-medium`}
              >
                Hands-on exercises
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4 pt-4 border-t border-slate-200/60">
            <div className="flex items-center justify-between mb-2">
              <span
                className={`${inter.className} text-sm font-semibold text-[#0E1B2E]`}
              >
                {completedTasks}/{totalTasks} Completed
              </span>
              <span
                className={`${inter.className} text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200`}
              >
                {Math.round(completionPercent)}%
              </span>
            </div>
            <div className="h-2.5 rounded-full overflow-hidden bg-slate-100 border border-slate-200/60">
              <div
                className="h-full bg-gradient-to-r from-[#0E1B2E] via-blue-600 to-indigo-600 transition-all duration-500 shadow-sm"
                style={{ width: `${completionPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* LIST */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="p-5 space-y-4">
            <div className="rounded-xl border-2 border-slate-200/60 shadow-sm bg-white/60 overflow-hidden">
              <button
                onClick={() => setTasksExpanded(!tasksExpanded)}
                className={`${inter.className} w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors`}
              >
                <div className="flex items-center space-x-2.5 mt-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                    <ListTree className="w-4 h-4 text-slate-600" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-semibold text-sm text-[#0E1B2E]">
                      All Tasks
                    </h3>
                    <span className="text-xs text-slate-600 font-medium">
                      {totalTasks} available
                    </span>
                  </div>
                </div>
                {tasksExpanded ? (
                  <ChevronUp className="w-4 h-4 text-slate-600" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-600" />
                )}
              </button>

              {tasksExpanded && (
                <nav className="p-3 mt-2 space-y-2 border-t-2 border-slate-200/60">
                  {practiceTasks.length > 0 ? (
                    practiceTasks.map((task: any) => {
                      const isCompleted = completionMap[task.question_number];
                      const isSelected =
                        selectedPracticeTask === task.question_number;
                      return (
                        <button
                          key={task.question_number}
                          onClick={() =>
                            onSelectPracticeTask?.(task.question_number)
                          }
                          className={`${inter.className} w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all group text-left ${
                            isSelected
                              ? "bg-[#0E1B2E] text-white shadow-lg"
                              : "hover:bg-slate-50 text-[#0E1B2E] border-2 border-transparent hover:border-blue-200"
                          }`}
                        >
                          <div
                            className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-[10px] flex-shrink-0 ${isSelected ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600"}`}
                          >
                            {task.question_number}
                          </div>
                          <div className="flex-1 min-w-0 flex items-center gap-2">
                            <div className="font-semibold truncate flex-1">
                              {task.title || `Task #${task.question_number}`}
                            </div>

                            {task.difficulty && (
                              <span
                                className={`text-xs px-4 py-1 rounded border text-[10px] flex items-center justify-center tracking-wide w-12 h-[18px] ${
                                  isSelected
                                    ? "border-white/20 bg-white/10"
                                    : getDifficultyColor(task.difficulty)
                                }`}
                              >
                                {task.difficulty === "Intermediate"
                                  ? "Medium"
                                  : task.difficulty}
                              </span>
                            )}
                          </div>

                          {isCompleted && !isSelected && (
                            <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                          )}
                          {isSelected && (
                            <ChevronRight className="w-4 h-4 text-white flex-shrink-0" />
                          )}
                        </button>
                      );
                    })
                  ) : (
                    <p className="text-center py-4 text-xs text-slate-400">
                      Loading tasks...
                    </p>
                  )}
                </nav>
              )}
            </div>
          </div>
        </div>
      </aside>
    );
  }

  const totalTutorials = tutorialsCount ?? 0;
  const totalChallenges = challengesCount ?? 0;

  const completedTuts = completedTutorials ?? 0;
  const completedChals = completedChallenges ?? 0;

  const progress =
    activeMode === "tutorials"
      ? totalTutorials > 0
        ? (completedTuts / totalTutorials) * 100
        : 0
      : totalChallenges > 0
        ? (completedChals / totalChallenges) * 100
        : 0;

  return (
    <aside className="flex-shrink-0 space-y-5 max-h-screen overflow-y-auto pr-2 custom-scrollbar">
      {/* BUG FIX OVERVIEW */}
      <div className="rounded-2xl p-5 bg-white/70 border-2 border-slate-200/60 shadow-lg shadow-slate-200/30">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-md">
            <Bug className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3
              className={`${inter.className} font-bold text-base text-[#0E1B2E]`}
            >
              Bug Fix Training
            </h3>
            <p
              className={`${inter.className} text-xs text-slate-600 font-medium`}
            >
              Debug real issues
            </p>
          </div>
        </div>

        {/* COUNTS */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl p-3 bg-gradient-to-br from-blue-50 to-indigo-50 text-center border-2 border-blue-200/60">
            <p
              className={`${inter.className} text-xs text-blue-600 font-semibold mb-1`}
            >
              Tutorials
            </p>
            <p
              className={`${inter.className} text-2xl font-bold text-blue-700`}
            >
              {tutorialsCount ?? 0}
            </p>
          </div>
          <div className="rounded-xl p-3 bg-gradient-to-br from-amber-50 to-orange-50 text-center border-2 border-amber-200/60">
            <p
              className={`${inter.className} text-xs text-amber-600 font-semibold mb-1`}
            >
              Challenges
            </p>
            <p
              className={`${inter.className} text-2xl font-bold text-amber-700`}
            >
              {challengesCount ?? 0}
            </p>
          </div>
        </div>

        {/* PROGRESS BAR */}
        <div className="mt-4">
          <div
            className={`${inter.className} flex justify-between text-xs font-semibold mb-2`}
          >
            <span className="text-[#0E1B2E]">
              {activeMode === "tutorials"
                ? "Tutorial Progress"
                : "Challenge Progress"}
            </span>
            <span className="text-blue-600">{Math.round(progress)}%</span>
          </div>
          <div className="h-2.5 rounded-full overflow-hidden bg-slate-100 border border-slate-200/60">
            <div
              className="h-full bg-gradient-to-r from-[#0E1B2E] to-blue-600 transition-all duration-500 shadow-sm"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* DEBUG WORKFLOW */}
      <div className="rounded-2xl p-5 bg-gradient-to-br from-blue-50/50 to-white border-2 border-blue-200/60 shadow-md">
        <h3
          className={`${inter.className} font-bold text-sm mb-4 flex items-center gap-2 text-[#0E1B2E]`}
        >
          <span>🧠</span>
          <span>Debug Workflow</span>
        </h3>

        <ol className={`${inter.className} text-xs space-y-2.5 text-slate-700`}>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
              1
            </span>
            <span className="pt-0.5">
              Understand expected vs actual behavior
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
              2
            </span>
            <span className="pt-0.5">Reproduce the issue reliably</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
              3
            </span>
            <span className="pt-0.5">Inspect logs & state</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
              4
            </span>
            <span className="pt-0.5">Identify root cause</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
              5
            </span>
            <span className="pt-0.5">Apply minimal fix & retest</span>
          </li>
        </ol>
      </div>

      {/* COMMON BUG TYPES */}
      <div className="rounded-2xl p-5 bg-gradient-to-br from-amber-50/50 to-white border-2 border-amber-200/60 shadow-md">
        <h3
          className={`${inter.className} font-bold text-sm mb-4 flex items-center gap-2 text-[#0E1B2E]`}
        >
          <span>🐞</span>
          <span>Common Bug Patterns</span>
        </h3>

        <ul className={`${inter.className} text-xs space-y-2.5 text-slate-700`}>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>State & lifecycle issues</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>Async / race conditions</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>Incorrect assumptions</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>Edge cases & null handling</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>Environment-specific bugs</span>
          </li>
        </ul>
      </div>
    </aside>
  );
}

return (
  <aside className="flex-shrink-0">
    <div className="rounded-2xl p-5 mb-5 bg-white/70 border-2 border-slate-200/60 shadow-lg shadow-slate-200/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0E1B2E] to-blue-900 flex items-center justify-center shadow-md">
          <BookOpen className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3
            className={`${inter.className} font-bold text-base text-[#0E1B2E]`}
          >
            Navigation
          </h3>
          <p
            className={`${inter.className} text-xs text-slate-600 font-medium`}
          >
            Learn the basics
          </p>
        </div>
      </div>
      <nav className="space-y-2">
        <button
          className={`${inter.className} w-full text-left px-4 py-3 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white shadow-md`}
        >
          Reading & Overview
        </button>
        <button
          className={`${inter.className} w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-colors hover:bg-slate-50 text-slate-700 border-2 border-slate-200 hover:border-slate-300`}
        >
          <Users className="w-4 h-4 inline mr-2" />
          Know Your Team
        </button>
      </nav>
    </div>
  </aside>
);
