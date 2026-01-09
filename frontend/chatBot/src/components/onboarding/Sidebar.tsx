'use client';

import { useState, useEffect } from 'react';
import { BookOpen, Users, Sparkles, ListTree, ChevronRight, Bug, ChevronDown, ChevronUp } from 'lucide-react';

interface SidebarProps {
  completedModules: number;
  totalModules: number;
  activeTab: string;             
  practiceTasks?: any[];
  selectedPracticeTask?: number | null;
  onSelectPracticeTask?: (key: number) => void;
  tutorialsCount?: number;
  challengesCount?: number;
  activeMode?: 'tutorials' | 'challenges';
  onSwitchMode?: (mode: 'tutorials' | 'challenges') => void;
}

export default function Sidebar({
  completedModules,
  totalModules,
  activeTab,
  practiceTasks = [],
  selectedPracticeTask = null,
  onSelectPracticeTask,
  tutorialsCount,
  challengesCount,
  activeMode,
  onSwitchMode
}: SidebarProps) {

  // Track practice task completion status from localStorage
  const [completionMap, setCompletionMap] = useState<Record<number, boolean>>({});
  const [tasksExpanded, setTasksExpanded] = useState<boolean>(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("onboard_practice_progress");
      if (raw) setCompletionMap(JSON.parse(raw));
    } catch {
      // ignore
    }
  }, []);

  // ------------------------------------------------------------------
  //     IF ACTIVE TAB IS PRACTICE → SHOW PRACTICE SIDEBAR
  // ------------------------------------------------------------------
  if (activeTab === "practice") {
    // Calculate practice stats
    const completedTasks = practiceTasks?.filter((t: any) => t._completed).length || 0;
    const totalTasks = practiceTasks?.length || 0;
    const completionPercent = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

    return (
      <aside className="col-span-3 flex flex-col border-r border-gray-200 bg-white" style={{ height: 'calc(100vh - 180px)' }}>

        {/* PRACTICE HEADER CARD */}
        <div className="p-4 border-b border-gray-200 flex-shrink-0">
          <h3 className="font-semibold mb-1.5 flex items-center space-x-2 text-base text-[#0E1B2E]">
            <Sparkles className="w-4 h-4 text-[#0E1B2E]" />
            <span>Practice Tasks</span>
          </h3>

          <p className="text-xs text-[#0E1B2E]/60">
            Master the codebase with hands-on exercises
          </p>

          {/* Progress Stats */}
          <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between">
            <span className="text-sm font-semibold text-[#0E1B2E]">
              {completedTasks}/{totalTasks} Completed
            </span>
            <span className="text-xs text-[#0E1B2E]/60">{Math.round(completionPercent)}%</span>
          </div>

          <div className="h-2 rounded-full overflow-hidden mt-2 bg-[#0E1B2E]/10">
            <div
              className="h-full bg-[#0E1B2E] transition-all duration-500"
              style={{ width: `${completionPercent}%` }}
            />
          </div>
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4 space-y-4">
            {/* TASK LIST */}
            <div className="rounded-lg border border-gray-200 shadow-sm bg-white">
              <button
                onClick={() => setTasksExpanded(!tasksExpanded)}
                className="w-full flex items-center justify-between p-4 hover:bg-[#0E1B2E]/5 transition-colors rounded-t-lg"
              >
                <div className="flex items-center space-x-2">
                  <ListTree className="w-4 h-4 text-[#0E1B2E]" />
                  <h3 className="font-semibold text-base text-[#0E1B2E]">
                    Practice Tasks
                  </h3>
                  <span className="text-xs text-[#0E1B2E]/60 font-normal">
                    ({totalTasks})
                  </span>
                </div>
                {tasksExpanded ? (
                  <ChevronUp className="w-4 h-4 text-[#0E1B2E]/60" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-[#0E1B2E]/60" />
                )}
              </button>

              {tasksExpanded && (
                <nav className="p-4 pt-0 space-y-2 border-t border-gray-200">
            {practiceTasks && practiceTasks.length > 0 ? (
              practiceTasks.map((task: any) => {
                const isCompleted = completionMap[task.question_number];
                const isSelected = selectedPracticeTask === task.question_number;
                const difficultyColor =
                  task.difficulty === "Easy"
                    ? "bg-green-100 text-green-700"
                    : task.difficulty === "Intermediate"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-red-100 text-red-700";

                return (
                  <button
                    key={task.question_number}
                    onClick={() => onSelectPracticeTask?.(task.question_number)}
                    className={`
                      w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors group
                      ${
                        isSelected
                          ? "bg-[#0E1B2E] border-2 border-[#0E1B2E] text-white"
                          : isCompleted
                          ? "bg-green-50 border border-green-200 text-green-700"
                          : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] border border-transparent"
                      }
                    `}
                  >
                    {/* Task Number and Title */}
                    <div className="flex-1 text-left min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold ${isSelected ? 'text-white' : 'text-[#0E1B2E]'}`}>
                          Task #{task.question_number}
                        </span>
                      </div>
                      {task.steps && (
                        <span className={`text-xs ml-1 ${isSelected ? 'text-white/80' : 'text-[#0E1B2E]/60'}`}>
                          ({task.steps.length} steps)
                        </span>
                      )}
                    </div>

                    {/* Completion Check */}
                    {isCompleted && !isSelected && (
                      <span className="text-green-600 font-bold">✓</span>
                    )}

                    {/* Selected Indicator */}
                    {isSelected && (
                      <span className="text-xs font-bold text-white">
                        →
                      </span>
                    )}

                    {/* Hover Indicator */}
                    {!isCompleted && !isSelected && (
                      <ChevronRight className="w-4 h-4 text-[#0E1B2E]/40 group-hover:text-[#0E1B2E]/60 transition-all" />
                    )}
                  </button>
                );
              })
            ) : (
              <p className="text-xs text-[#0E1B2E]/60 py-4 text-center">
                No tasks available yet
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

  // ------------------------------------------------------------------
  //     IF ACTIVE TAB IS BUG FIX → SHOW BUG FIX SIDEBAR
// ------------------------------------------------------------------
if (activeTab === "bugfix") {
  const total = (tutorialsCount ?? 0) + (challengesCount ?? 0);
  const progress =
    total > 0
      ? activeMode === "tutorials"
        ? (tutorialsCount! / total) * 100
        : (challengesCount! / total) * 100
      : 0;

  return (
    <aside className="col-span-3 space-y-4 max-h-screen overflow-y-auto pr-2">

        {/* BUG FIX OVERVIEW */}
        <div className="rounded-lg p-4 bg-white border border-gray-200 shadow-sm">
          <h3 className="font-semibold flex items-center gap-2 text-base">
            <Bug className="w-4 h-4 text-gray-700" />
          <span>Bug Fix Training</span>
        </h3>

          <p className="text-xs mt-1 text-gray-600">
          Debug real-world issues & broken flows
        </p>

        {/* COUNTS */}
        <div className="mt-3 grid grid-cols-2 gap-3">
            <div className="rounded-lg p-2 bg-gray-50 text-center border border-gray-200">
              <p className="text-xs text-gray-500">Tutorials</p>
              <p className="text-lg font-bold text-gray-700">
              {tutorialsCount ?? 0}
            </p>
          </div>
            <div className="rounded-lg p-2 bg-gray-50 text-center border border-gray-200">
              <p className="text-xs text-gray-500">Challenges</p>
              <p className="text-lg font-bold text-gray-700">
              {challengesCount ?? 0}
            </p>
          </div>
        </div>

        {/* PROGRESS BAR */}
        <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Mode Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
            <div className="h-2 rounded-full overflow-hidden bg-gray-200">
            <div
                className="h-full bg-gray-600 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

        {/* MODE SWITCH */}
        <div className="rounded-lg p-3 bg-white border border-gray-200 shadow-sm">
          <h4 className="text-sm font-semibold mb-2">Focus Mode</h4>

        <div className="grid grid-cols-2 gap-2">
          {(["tutorials", "challenges"] as const).map((mode) => {
            const isActive = activeMode === mode;

            return (
              <button
                key={mode}
                onClick={() => onSwitchMode?.(mode)}
                className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                      ? "bg-gray-800 text-white"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                }`}
              >
                {mode === "tutorials" ? "🎓 Tutorials" : "🎯 Challenges"}
              </button>
            );
          })}
        </div>
      </div>

        {/* DEBUG WORKFLOW */}
        <div className="rounded-lg p-4 bg-white border border-gray-200 shadow-sm">
          <h3 className="font-semibold text-base mb-2 flex items-center gap-2">
          <span>🧠</span>
          <span>Debug Workflow</span>
        </h3>

          <ol className="text-xs space-y-2 text-gray-600">
          <li>1. Understand expected vs actual behavior</li>
          <li>2. Reproduce the issue reliably</li>
          <li>3. Inspect logs & state</li>
          <li>4. Identify root cause</li>
          <li>5. Apply minimal fix & retest</li>
        </ol>
      </div>

        {/* COMMON BUG TYPES */}
        <div className="rounded-lg p-4 bg-white border border-gray-200 shadow-sm">
          <h3 className="font-semibold text-base mb-2 flex items-center gap-2">
          <span>🐞</span>
          <span>Common Bug Patterns</span>
        </h3>

          <ul className="text-xs space-y-2 text-gray-600">
          <li>→ State & lifecycle issues</li>
          <li>→ Async / race conditions</li>
          <li>→ Incorrect assumptions</li>
          <li>→ Edge cases & null handling</li>
          <li>→ Environment-specific bugs</li>
        </ul>
      </div>

    </aside>
  );
}

  // ------------------------------------------------------------------
  //     OTHERWISE → NORMAL READING SIDEBAR
  // ------------------------------------------------------------------
  return (
    <aside className="col-span-3">
      <div className="rounded-lg p-4 mb-4 bg-white border border-gray-200 shadow-sm">
        <h3 className="font-semibold mb-1.5 flex items-center space-x-2 text-base">
          <BookOpen className="w-4 h-4" />
          <span>Navigation</span>
        </h3>
        <p className="text-xs mb-3 text-gray-600">
          Learn the basics
        </p>
        <nav className="space-y-2">
          <button className="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold bg-gray-800 text-white">
            Reading & Overview
          </button>
          <button className="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors hover:bg-gray-50 text-gray-700">
            <Users className="w-3.5 h-3.5 inline mr-1.5" />
            Know Your Team
          </button>
        </nav>
      </div>
    </aside>
  );
}