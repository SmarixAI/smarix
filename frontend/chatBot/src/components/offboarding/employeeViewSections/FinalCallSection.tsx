"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Clock,
  Phone,
  HelpCircle,
  ExternalLink,
  Filter,
  Target,
  Info,
  ArrowUpCircle,
  User,
} from "lucide-react";
import Loader from "../Loader";
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

/* ================= TYPES ================= */

type Task = {
  id: string;
  title?: string;
  description?: string;
  priority: "High" | "Medium" | "Low";
  tags: string[];
  source: "AI" | "Manager";
  reference?: string;
  questions?: string[];
  estimated_time_minutes?: number;
  knowledge_capture_method?: string;
  ai_analyzed?: boolean;
  suggested_recipient?: string;
  suggested_recipient_reason?: string;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
  initialTasksData?: { employees?: any[] } | null;
  onTasksUpdated?: () => void;
};

/* ================= PRIORITY STYLES ================= */

const getPriorityStyles = (priority: Task["priority"]): string => {
  return priority === "High"
    ? "bg-red-50 text-red-700 border-red-200"
    : priority === "Medium"
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : "bg-emerald-50 text-emerald-700 border-emerald-200";
};

/* ================= COMPONENT ================= */

export default function EmployeeFinalCallSection({
  employeeId,
  darkMode = false,
  initialTasksData,
  onTasksUpdated,
}: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(
    new Set(),
  );
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(
    new Set(),
  );
  const [activeFilter, setActiveFilter] = useState<
    "all" | "high" | "medium" | "low"
  >("all");

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === "all") return true;
    return task.priority.toLowerCase() === activeFilter;
  });

  /* ================= LOAD DATA ================= */
  const hasParentData = initialTasksData !== undefined;

  useEffect(() => {
    if (hasParentData) {
      if (initialTasksData == null) {
        setLoading(true);
        setTasks([]);
        return;
      }
      const employee =
        initialTasksData.employees?.find(
          (e: any) => String(e.employeeId) === String(employeeId),
        ) ?? initialTasksData.employees?.[0];
      if (employee) {
        const aiTasks = (employee.tasks?.ai ?? []).filter((t: Task) =>
          t.id.startsWith("FC"),
        );
        const managerTasks = (employee.tasks?.manager ?? []).map(
          (t: any) => ({ ...t, tags: t.tags || ["Managerial"] }),
        );
        setTasks([...aiTasks, ...managerTasks]);
      }
      setLoading(false);
      return;
    }

    setLoading(true);
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/offboarding/tasks?employeeId=${encodeURIComponent(employeeId)}`);
        const data = await response.json();
        const employee =
          data.employees?.find(
            (e: any) => String(e.employeeId) === String(employeeId),
          ) ?? data.employees?.[0];

        if (employee) {
          const aiTasks = (employee.tasks?.ai ?? []).filter((t: Task) =>
            t.id.startsWith("FC"),
          );
          const managerTasks = (employee.tasks?.manager ?? []).map(
            (t: any) => ({ ...t, tags: t.tags || ["Managerial"] }),
          );
          setTasks([...aiTasks, ...managerTasks]);
        }
      } catch (error) {
        console.error("Error fetching final call tasks:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [employeeId, hasParentData, initialTasksData]);

  const toggleTaskDetails = (taskId: string) => {
    setExpandedTaskIds((prev) => {
      const newSet = new Set(prev);
      newSet.has(taskId) ? newSet.delete(taskId) : newSet.add(taskId);
      return newSet;
    });
  };

  const getTaskTitle = (task: Task): string => {
    if (task.title) return task.title;
    let clean = (task.description || "")
      .replace(/\*\*/g, "")
      .replace(/#{1,6}\s*/g, "")
      .trim();
    const firstPhrase = clean.split(/[.:\n]/)[0].trim();
    return firstPhrase.length > 0 && firstPhrase.length < 60
      ? firstPhrase
      : clean.substring(0, 60) + "...";
  };

  if (loading)
    return (
      <Loader
        darkMode={false}
        message="Analyzing final requirements..."
        size="md"
      />
    );

  return (
    <div className="w-full h-full flex flex-col pt-6 pb-0">
      {/* Main Container */}
      <div className="flex-1 w-full rounded-[2rem] border-2 border-slate-200 shadow-lg bg-white flex flex-col min-h-0 overflow-hidden">
        {/* Header - Matching Documentation Style */}
        <div className="px-8 py-6 border-b-2 border-slate-200 bg-gradient-to-r from-slate-50 to-blue-50/30 flex justify-between items-center">
          <div>
            <h2
              className={`${inter.className} text-xl font-bold text-[#0E1B2E]`}
            >
              Final Call Tasks
            </h2>
            <p className="text-sm text-slate-600 mt-1 font-medium">
              Critical items to explain before departure
            </p>
          </div>

          <div className="flex gap-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
            {["all", "high", "medium", "low"].map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f as any)}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all uppercase tracking-widest ${
                  activeFilter === f
                    ? "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white shadow-md"
                    : "text-slate-400 hover:text-slate-600"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-y-auto divide-y-2 divide-slate-200">
          {filteredTasks.map((task) => {
            const isDone = completedTaskIds.has(task.id);
            const isExpanded = expandedTaskIds.has(task.id);

            return (
              <div
                key={task.id}
                className={`transition-all duration-300 ${isDone ? "bg-emerald-50/10" : isExpanded ? "bg-slate-50/50" : ""}`}
              >
                {/* Updated padding to py-5 to match HandoverSection */}
                <div className="px-8 py-5">
                  <div className="flex justify-between items-center gap-6">
                    <div
                      className="flex-1 cursor-pointer flex items-center gap-4"
                      onClick={() => toggleTaskDetails(task.id)}
                    >
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center border-2 ${isDone ? "bg-emerald-100 border-emerald-200 text-emerald-600" : "bg-white border-slate-200 text-slate-400 shadow-sm"}`}
                      >
                        {isDone ? (
                          <CheckCircle className="w-6 h-6" />
                        ) : (
                          <Phone className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <h4
                          className={`${inter.className} text-base font-bold text-[#0E1B2E] flex items-center gap-3`}
                        >
                          {getTaskTitle(task)}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5">
                          <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wide">
                            ID: {task.id}
                          </p>
                          <span className="text-slate-300 text-xs">•</span>
                          <span className="text-[11px] text-slate-400 font-bold uppercase">
                            {task.source}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {isDone ? (
                        <>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(
                              task.priority,
                            )}`}
                          >
                            {task.priority}
                          </span>
                          <span
                            className={`${inter.className} flex items-center gap-1.5 text-xs font-bold text-green-700 bg-green-50 px-3 py-2 rounded-xl border-2 border-green-200 animate-in fade-in zoom-in-95`}
                          >
                            <CheckCircle className="w-4 h-4" />
                            Explained
                          </span>
                        </>
                      ) : (
                        <>
                        <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(
                              task.priority,
                            )}`}
                          >
                            {task.priority}
                          </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setCompletedTaskIds((prev) =>
                              new Set(prev).add(task.id),
                            );
                          }}
                          className={`${inter.className} flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white transition-all bg-gradient-to-r from-[#0E1B2E] to-blue-900 hover:shadow-lg active:scale-95`}
                        >
                          <CheckCircle className="w-4 h-4" />
                          <span>Mark as Explained</span>
                        </button>
                        </>
                      )}

                      <button
                        onClick={() => toggleTaskDetails(task.id)}
                        className="p-2 text-slate-300 hover:text-slate-600 transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    /* Updated margin to mb-2 to match HandoverSection */
                    <div className="mt-6 mb-2 animate-in fade-in slide-in-from-top-4 duration-300">
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 rounded-2xl bg-white border-2 border-slate-200 shadow-lg overflow-hidden">
                        {/* Left: Detail Panel */}
                        <div className="lg:col-span-7 p-8 space-y-8 border-r-2 border-slate-200">
                          <section>
                            <div className="flex items-center gap-2 mb-3 text-slate-400">
                              <Info className="w-4 h-4" />
                              <h5 className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                Task Overview
                              </h5>
                            </div>
                            <p className="text-sm text-slate-600 leading-relaxed font-medium">
                              {task.description
                                ?.replace(/\*\*/g, "")
                                .replace(/#{1,6}\s*/g, "")}
                            </p>
                          </section>

                          <section className="bg-slate-50/50 p-6 rounded-xl border-2 border-slate-200">
                            <div className="flex items-center gap-2 mb-4 text-blue-700">
                              <Target className="w-4 h-4" />
                              <h5 className="text-[10px] font-bold uppercase tracking-widest">
                                Key Points to Address
                              </h5>
                            </div>
                            <ul className="space-y-3">
                              {(
                                task.questions || [
                                  "Walkthrough of core logic",
                                  "Explain specific edge cases",
                                  "Identify potential future risks",
                                ]
                              ).map((q, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-[#0E1B2E] font-bold flex items-start gap-3"
                                >
                                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                                  <span>{q}</span>
                                </li>
                              ))}
                            </ul>
                          </section>
                        </div>

                        {/* Right: Successor & Metadata Panel */}
                        <div className="lg:col-span-5 p-8 bg-gradient-to-br from-white to-blue-50/20 flex flex-col justify-center gap-4">
                          {task && (
                            <div className="bg-white p-5 rounded-2xl border-2 border-blue-100 shadow-sm">
                              <div className="flex items-center gap-2 mb-3">
                                <User className="w-4 h-4 text-blue-600" />
                                <span className="text-[10px] font-black uppercase text-slate-800 tracking-tight">
                                  Suggested Final-Call Tip
                                </span>
                              </div>

                              <div
                                className={`${inter.className} text-sm text-blue-900 leading-relaxed`}
                              >
                                <span className="font-bold">
                                  Schedule a 30-minute live walkthrough
                                </span>
                                <span className="ml-1.5 text-blue-700/80 font-medium">
                                  covering the end-to-end deployment flow,
                                  critical failure points, rollback and recovery
                                  procedures, and clear ownership boundaries.
                                  Ensure the successor can independently deploy,
                                  debug, and escalate issues before marking this
                                  handover as complete.
                                </span>
                              </div>
                            </div>
                          )}
                          <div className="bg-white p-5 rounded-2xl border-2 border-slate-200 shadow-sm space-y-4">
                            <div>
                              <div className="flex items-center gap-2 mb-2 text-slate-400">
                                <ArrowUpCircle className="w-4 h-4" />
                                <span className="text-[10px] font-black uppercase tracking-tight text-slate-500">
                                  Method
                                </span>
                              </div>
                              <p
                                className={`${jetbrainsMono.className} text-[11px] font-bold text-blue-700 uppercase`}
                              >
                                {task.knowledge_capture_method ||
                                  "Interactive session"}
                              </p>
                            </div>

                            {task.reference && (
                              <div>
                                <div className="flex items-center gap-2 mb-2 text-slate-400">
                                  <ExternalLink className="w-4 h-4" />
                                  <span className="text-[10px] font-black uppercase tracking-tight text-slate-500">
                                    References
                                  </span>
                                </div>
                                <div className="space-y-1.5">
                                  {task.reference
                                    .split(", ")
                                    .map((ref, idx) => (
                                      <div
                                        key={idx}
                                        className="flex items-center gap-2 text-[10px] text-blue-900 font-bold bg-blue-50/50 p-2 rounded-lg border border-blue-100"
                                      >
                                        <div className="w-1 h-1 rounded-full bg-blue-400" />
                                        {ref}
                                      </div>
                                    ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
