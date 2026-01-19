"use client";

import { useEffect, useState } from "react";
import {
  UserPlus,
  XCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  ExternalLink,
  Clock,
  Plus,
  Filter,
  AlertCircle,
} from "lucide-react";
import Loader from "../Loader";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

/* ================= TYPES ================= */

type Task = {
  id: string;
  title: string;
  priority: "High" | "Medium" | "Low";
  tags: string[];
  source: "AI" | "Manager";
  status?: "active" | "inactive" | "not_needed";
  description?: string;
  questions?: string[];
  reference?: string;
  estimated_time_minutes?: number;
  knowledge_capture_method?: string;
};

type FinalCallSectionProps = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= PRIORITY STYLES ================= */

const getPriorityStyles = (
  priority: Task["priority"],
  darkMode: boolean
): string => {
  if (darkMode) {
    return priority === "High"
      ? "bg-red-900/40 text-red-200 border-red-800"
      : priority === "Medium"
      ? "bg-amber-900/40 text-amber-200 border-amber-800"
      : "bg-emerald-900/40 text-emerald-200 border-emerald-800";
  }
  return priority === "High"
    ? "bg-red-50 text-red-700 border-red-200"
    : priority === "Medium"
    ? "bg-amber-50 text-amber-700 border-amber-200"
    : "bg-emerald-50 text-emerald-700 border-emerald-200";
};

/* ================= COMPONENT ================= */

export default function FinalCallSection({
  employeeId,
  darkMode = false,
}: FinalCallSectionProps) {
  const [aiTasks, setAiTasks] = useState<Task[]>([]);
  const [managerTasks, setManagerTasks] = useState<Task[]>([]);
  const [updateCounter, setUpdateCounter] = useState(0);
  const [employeeStatus, setEmployeeStatus] = useState<string>("active");
  const [loading, setLoading] = useState(true);

  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newPriority, setNewPriority] = useState<"High" | "Medium" | "Low">(
    "Medium"
  );

  // Filter states
  const [priorityFilter, setPriorityFilter] = useState<
    "All" | "High" | "Medium" | "Low"
  >("All");
  const [showNotNeeded, setShowNotNeeded] = useState(false);

  // Expanded task IDs
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(
    new Set()
  );

  /* ================= SUMMARY DERIVED DATA ================= */

  const allTasks = [...aiTasks, ...managerTasks];
  const activeTasks = allTasks.filter((t) => t.status !== "not_needed");

  const summary = {
    total: activeTasks.length,
    high: activeTasks.filter((t) => t.priority === "High").length,
    medium: activeTasks.filter((t) => t.priority === "Medium").length,
    low: activeTasks.filter((t) => t.priority === "Low").length,
    notNeeded: allTasks.filter((t) => t.status === "not_needed").length,
    completed: 0,
    remaining: activeTasks.length,
    yetToAssign: activeTasks.length,
  };

  // Filter tasks based on selected filters
  const filteredAiTasks = aiTasks.filter((task) => {
    if (showNotNeeded) {
      if (task.status !== "not_needed") return false;
    } else {
      if (task.status === "not_needed") return false;
    }
    if (priorityFilter !== "All" && task.priority !== priorityFilter)
      return false;
    return true;
  });

  const filteredManagerTasks = managerTasks.filter((task) => {
    if (showNotNeeded) {
      if (task.status !== "not_needed") return false;
    } else {
      if (task.status === "not_needed") return false;
    }
    if (priorityFilter !== "All" && task.priority !== priorityFilter)
      return false;
    return true;
  });

  /* ================= LOAD TASKS ================= */

  useEffect(() => {
    setAiTasks([]);
    setManagerTasks([]);
    setUpdateCounter(0);
    setLoading(true);

    const fetchData = async () => {
      try {
        const empResponse = await fetch("/api/offboarding/employees");
        if (empResponse.ok) {
          const empData = await empResponse.json();
          const employee = empData.employees?.find(
            (e: any) => e.employeeId === employeeId
          );
          if (employee) {
            setEmployeeStatus(employee.status || "active");
          }
        }

        const response = await fetch("/api/offboarding/tasks");
        if (!response.ok) {
          console.error("Failed to fetch tasks data");
          setLoading(false);
          return;
        }
        const data = await response.json();

        if (!data?.employees?.length) {
          setLoading(false);
          return;
        }

        let employee = data.employees.find(
          (e: any) =>
            e.employeeId === employeeId ||
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
        );

        if (!employee) {
          employee = data.employees[0];
        }

        if (employee) {
          const isInactive =
            employeeStatus === "inactive" ||
            (employeeStatus !== "active" && employeeStatus !== "leaving");

          const aiTasksMap = new Map<string, Task>();
          (employee.tasks?.ai ?? []).forEach((task: any) => {
            if (!aiTasksMap.has(task.id)) {
              aiTasksMap.set(task.id, {
                ...task,
                tags: task.tags || ["Manual"],
                status: task.status || (isInactive ? "not_needed" : "active"),
              });
            }
          });

          const managerTasksMap = new Map<string, Task>();
          (employee.tasks?.manager ?? []).forEach((task: any) => {
            if (!managerTasksMap.has(task.id)) {
              managerTasksMap.set(task.id, {
                ...task,
                tags: task.tags || ["Manual"],
                status: task.status || (isInactive ? "not_needed" : "active"),
              });
            }
          });

          setAiTasks(Array.from(aiTasksMap.values()));
          setManagerTasks(Array.from(managerTasksMap.values()));
        } else {
          setAiTasks([]);
          setManagerTasks([]);
        }
      } catch (error) {
        console.error("Error fetching tasks data:", error);
        setAiTasks([]);
        setManagerTasks([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= ACTION HANDLERS ================= */

  const updatePriority = async (
    id: string,
    source: Task["source"],
    newPriority: Task["priority"]
  ) => {
    const oldPriority =
      source === "AI"
        ? aiTasks.find((t) => t.id === id)?.priority
        : managerTasks.find((t) => t.id === id)?.priority;

    if (source === "AI") {
      setAiTasks((prev) => {
        const updated = prev.map((t) =>
          t.id === id ? { ...t, priority: newPriority } : t
        );
        return updated;
      });
    } else {
      setManagerTasks((prev) => {
        const updated = prev.map((t) =>
          t.id === id ? { ...t, priority: newPriority } : t
        );
        return updated;
      });
    }
    setUpdateCounter((prev) => prev + 1);

    try {
      const response = await fetch("/api/offboarding/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employeeId: employeeId,
          taskId: id,
          priority: newPriority,
          source: source === "AI" ? "ai" : "manager",
        }),
      });

      if (!response.ok) {
        // Revert
        if (oldPriority) {
          if (source === "AI") {
            setAiTasks((prev) =>
              prev.map((t) =>
                t.id === id ? { ...t, priority: oldPriority } : t
              )
            );
          } else {
            setManagerTasks((prev) =>
              prev.map((t) =>
                t.id === id ? { ...t, priority: oldPriority } : t
              )
            );
          }
        }
      }
    } catch (error) {
      if (oldPriority) {
        if (source === "AI") {
          setAiTasks((prev) =>
            prev.map((t) => (t.id === id ? { ...t, priority: oldPriority } : t))
          );
        } else {
          setManagerTasks((prev) =>
            prev.map((t) => (t.id === id ? { ...t, priority: oldPriority } : t))
          );
        }
      }
    }
  };

  const markTaskAsNotNeeded = async (id: string, source: Task["source"]) => {
    if (source === "AI") {
      setAiTasks((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, status: "not_needed" as const } : t
        )
      );
    } else {
      setManagerTasks((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, status: "not_needed" as const } : t
        )
      );
    }
    setUpdateCounter((prev) => prev + 1);

    try {
      const response = await fetch("/api/offboarding/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employeeId: employeeId,
          taskId: id,
          status: "not_needed",
          source: source === "AI" ? "ai" : "manager",
        }),
      });

      if (!response.ok) {
        if (source === "AI") {
          setAiTasks((prev) =>
            prev.map((t) =>
              t.id === id ? { ...t, status: "active" as const } : t
            )
          );
        } else {
          setManagerTasks((prev) =>
            prev.map((t) =>
              t.id === id ? { ...t, status: "active" as const } : t
            )
          );
        }
      }
    } catch (error) {
      if (source === "AI") {
        setAiTasks((prev) =>
          prev.map((t) =>
            t.id === id ? { ...t, status: "active" as const } : t
          )
        );
      } else {
        setManagerTasks((prev) =>
          prev.map((t) =>
            t.id === id ? { ...t, status: "active" as const } : t
          )
        );
      }
    }
  };

  const assignHandover = (task: Task) => {
    console.log("Assign handover:", task.title);
  };

  const addManagerTask = async () => {
    if (!newTaskTitle.trim()) return;

    const taskTitle = newTaskTitle.trim();
    const taskPriority = newPriority;

    const tempId = crypto.randomUUID();
    const newTask = {
      id: tempId,
      title: taskTitle,
      priority: taskPriority,
      tags: ["Manual"],
      source: "Manager" as const,
    };

    setManagerTasks((prev) => [...prev, newTask]);
    setNewTaskTitle("");
    setNewPriority("Medium");

    try {
      const response = await fetch("/api/offboarding/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employeeId: employeeId,
          action: "add",
          title: taskTitle,
          priority: taskPriority,
        }),
      });

      if (!response.ok) {
        setManagerTasks((prev) => prev.filter((t) => t.id !== tempId));
        alert("Failed to save task. Please try again.");
      } else {
        const data = await response.json();
        if (data.task && data.task.id !== tempId) {
          setManagerTasks((prev) =>
            prev.map((t) => (t.id === tempId ? { ...t, id: data.task.id } : t))
          );
        }
      }
    } catch (error) {
      setManagerTasks((prev) => prev.filter((t) => t.id !== tempId));
      alert("Error saving task. Please try again.");
    }
  };

  /* ================= TASK ROW ================= */

  const toggleExpand = (taskId: string) => {
    setExpandedTaskIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const TaskRow = ({ task }: { task: Task }) => {
    const isExpanded = expandedTaskIds.has(task.id);
    const hasDetails =
      task.description ||
      task.questions?.length ||
      task.reference ||
      task.estimated_time_minutes ||
      task.knowledge_capture_method;

    return (
      <div
        className={`border-b last:border-b-0 transition-all duration-200 border-[#0E1B2E]/10 ${
          darkMode ? "border-gray-700" : ""
        }`}
      >
        {/* MAIN ROW */}
        <div
          className={`px-4 py-3 flex justify-between items-start gap-4 transition-all duration-200 ${
            darkMode ? "hover:bg-gray-800/50" : "hover:bg-blue-50/30"
          } ${
            isExpanded ? (darkMode ? "bg-gray-800/30" : "bg-blue-50/50") : ""
          }`}
        >
          {/* LEFT */}
          <div
            className="flex-1 cursor-pointer"
            onClick={() => hasDetails && toggleExpand(task.id)}
          >
            <div className="flex items-start gap-3">
              {hasDetails && (
                <div className="mt-0.5 text-slate-400">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              )}
              <div className="flex-1">
                <p
                  className={`font-semibold text-sm ${
                    darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                  }`}
                >
                  {task.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
                      task.source === "AI"
                        ? darkMode
                          ? "bg-purple-900/30 text-purple-200 border-purple-800"
                          : "bg-purple-50 text-purple-700 border-purple-100"
                        : darkMode
                        ? "bg-blue-900/30 text-blue-200 border-blue-800"
                        : "bg-blue-50 text-blue-700 border-blue-100"
                    }`}
                  >
                    {task.source}
                  </span>
                  <span
                    className={`text-xs ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}
                  >
                    • {(task.tags || ["Manual"]).join(", ")}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT */}
          <div
            className="flex items-center gap-2 flex-shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            {/* PRIORITY DROPDOWN */}
            <select
              value={task.priority}
              onChange={(e) =>
                updatePriority(
                  task.id,
                  task.source,
                  e.target.value as Task["priority"]
                )
              }
              className={`
                px-2 py-1 rounded-md text-xs font-bold border cursor-pointer outline-none focus:ring-2 focus:ring-opacity-50
                transition-all duration-200
                ${getPriorityStyles(task.priority, darkMode)}
              `}
            >
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>

            {/* ASSIGN HANDOVER */}
            <button
              onClick={() => assignHandover(task)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white shadow-sm transition-all
                ${
                  darkMode
                    ? "bg-blue-600 hover:bg-blue-700"
                    : "bg-[#0E1B2E] hover:bg-blue-900"
                }
              `}
            >
              <UserPlus className="w-3.5 h-3.5" />
              Assign
            </button>

            {/* NOT NEEDED */}
            {task.status !== "not_needed" && (
              <button
                onClick={() => markTaskAsNotNeeded(task.id, task.source)}
                className={`
                  p-1.5 rounded-lg transition-colors
                  ${
                    darkMode
                      ? "text-gray-400 hover:text-red-400 hover:bg-red-900/20"
                      : "text-slate-400 hover:text-red-600 hover:bg-red-50"
                  }
                `}
                title="Mark as Not Needed"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* EXPANDED DETAILS */}
        {isExpanded && hasDetails && (
          <div
            className={`px-4 py-3 border-t border-dashed border-[#0E1B2E]/10 ${
              darkMode ? "bg-gray-800/20" : "bg-slate-50/50"
            }`}
          >
            <div className="space-y-4 pl-7">
              {/* DESCRIPTION */}
              {task.description && (
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <FileText
                      className={`w-3.5 h-3.5 ${
                        darkMode ? "text-gray-400" : "text-slate-500"
                      }`}
                    />
                    <h4
                      className={`text-xs font-bold uppercase tracking-wider ${
                        darkMode ? "text-gray-300" : "text-slate-700"
                      }`}
                    >
                      Description
                    </h4>
                  </div>
                  <div
                    className={`text-xs whitespace-pre-wrap leading-relaxed ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}
                  >
                    {task.description
                      .replace(/\*\*/g, "")
                      .replace(/#{1,6}\s*/g, "")}
                  </div>
                </div>
              )}

              {/* QUESTIONS */}
              {task.questions && task.questions.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <HelpCircle
                      className={`w-3.5 h-3.5 ${
                        darkMode ? "text-gray-400" : "text-slate-500"
                      }`}
                    />
                    <h4
                      className={`text-xs font-bold uppercase tracking-wider ${
                        darkMode ? "text-gray-300" : "text-slate-700"
                      }`}
                    >
                      Key Questions
                    </h4>
                  </div>
                  <ul className="space-y-1">
                    {task.questions.map((q, idx) => (
                      <li
                        key={idx}
                        className={`text-xs flex items-start gap-2 ${
                          darkMode ? "text-gray-400" : "text-slate-600"
                        }`}
                      >
                        <span className="mt-0.5">•</span>
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* METADATA FOOTER */}
              <div
                className={`flex flex-wrap gap-4 pt-2 ${
                  darkMode ? "text-gray-500" : "text-slate-400"
                }`}
              >
                {task.reference && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <ExternalLink className="w-3 h-3" />
                    <span>
                      References:{" "}
                      <span
                        className={
                          darkMode ? "text-gray-300" : "text-slate-600"
                        }
                      >
                        {task.reference}
                      </span>
                    </span>
                  </div>
                )}
                {task.estimated_time_minutes && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <Clock className="w-3 h-3" />
                    <span>
                      Est. Time:{" "}
                      <span
                        className={
                          darkMode ? "text-gray-300" : "text-slate-600"
                        }
                      >
                        {task.estimated_time_minutes} min
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading tasks..." size="md" />;
  }

  return (
    <div className={`space-y-4 p-1 ${inter.className}`}>
      {/* ================= FILTERS ================= */}
      <div
        className={`rounded-xl border px-4 py-3 flex flex-wrap items-center justify-between gap-4 transition-colors ${
          darkMode
            ? "border-gray-700 bg-gray-800/50"
            : "border-slate-200 bg-white shadow-sm"
        }`}
      >
        <div className="flex items-center gap-2">
          <Filter
            className={`w-4 h-4 ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}
          />
          <span
            className={`text-sm font-semibold ${
              darkMode ? "text-gray-200" : "text-[#0E1B2E]"
            }`}
          >
            Filters
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label
              className={`text-xs font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}
            >
              Priority:
            </label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as any)}
              className={`
                px-2.5 py-1.5 rounded-lg text-xs font-medium border outline-none focus:ring-2
                transition-all cursor-pointer
                ${
                  darkMode
                    ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                    : "border-slate-200 bg-slate-50 text-slate-700 focus:ring-blue-500/20 hover:border-slate-300"
                }
              `}
            >
              <option value="All">All Priorities</option>
              <option value="High">High Only</option>
              <option value="Medium">Medium Only</option>
              <option value="Low">Low Only</option>
            </select>
          </div>

          <div
            className={`h-4 w-px ${darkMode ? "bg-gray-700" : "bg-slate-200"}`}
          ></div>

          <label className="flex items-center gap-2 cursor-pointer group">
            <div className="relative flex items-center">
              <input
                type="checkbox"
                checked={showNotNeeded}
                onChange={(e) => setShowNotNeeded(e.target.checked)}
                className="peer sr-only"
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors ${
                  darkMode
                    ? "bg-gray-700 peer-checked:bg-blue-600"
                    : "bg-slate-200 peer-checked:bg-[#0E1B2E]"
                }`}
              ></div>
              <div className="absolute left-1 top-1 bg-white w-3 h-3 rounded-full transition-transform peer-checked:translate-x-4"></div>
            </div>
            <span
              className={`text-xs font-medium ${
                darkMode
                  ? "text-gray-300"
                  : "text-slate-600 group-hover:text-[#0E1B2E]"
              }`}
            >
              Show Archived{" "}
              <span className="opacity-50">({summary.notNeeded})</span>
            </span>
          </label>
        </div>
      </div>

      {/* 🤖 AI TASKS */}
      <div
        className={`rounded-xl border overflow-hidden transition-colors ${
          darkMode
            ? "border-gray-700 bg-gray-800/30"
            : "border-slate-200 bg-white shadow-sm"
        }`}
      >
        <div
          className={`px-5 py-3 border-b flex items-center justify-between ${
            darkMode
              ? "border-gray-700 bg-gray-800/80"
              : "border-slate-100 bg-slate-50/50"
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">🤖</span>
            <h3
              className={`font-bold text-sm ${
                darkMode ? "text-gray-100" : "text-[#0E1B2E]"
              }`}
            >
              AI-Suggested Tasks
            </h3>
          </div>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              darkMode
                ? "bg-gray-700 text-gray-300"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {filteredAiTasks.length}
          </span>
        </div>

        <div
          className={
            darkMode ? "divide-y divide-gray-700" : "divide-y divide-slate-100"
          }
        >
          {filteredAiTasks.length > 0 ? (
            filteredAiTasks.map((task) => (
              <TaskRow key={`ai-${task.id}`} task={task} />
            ))
          ) : (
            <div className="p-8 text-center flex flex-col items-center justify-center gap-2 opacity-60">
              <div
                className={`p-3 rounded-full ${
                  darkMode ? "bg-gray-800" : "bg-slate-50"
                }`}
              >
                <AlertCircle className="w-6 h-6 text-slate-400" />
              </div>
              <p
                className={`text-sm ${
                  darkMode ? "text-gray-400" : "text-slate-500"
                }`}
              >
                No AI tasks found matching your filters.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 👤 MANAGER TASKS */}
      <div
        className={`rounded-xl border overflow-hidden transition-colors ${
          darkMode
            ? "border-gray-700 bg-gray-800/30"
            : "border-slate-200 bg-white shadow-sm"
        }`}
      >
        <div
          className={`px-5 py-3 border-b flex items-center justify-between ${
            darkMode
              ? "border-gray-700 bg-gray-800/80"
              : "border-slate-100 bg-slate-50/50"
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">👤</span>
            <h3
              className={`font-bold text-sm ${
                darkMode ? "text-gray-100" : "text-[#0E1B2E]"
              }`}
            >
              Manager-Added Tasks
            </h3>
          </div>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              darkMode
                ? "bg-gray-700 text-gray-300"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {filteredManagerTasks.length}
          </span>
        </div>

        <div
          className={
            darkMode ? "divide-y divide-gray-700" : "divide-y divide-slate-100"
          }
        >
          {filteredManagerTasks.length > 0 ? (
            filteredManagerTasks.map((task) => (
              <TaskRow key={`manager-${task.id}`} task={task} />
            ))
          ) : (
            <div className="p-6 text-center text-xs text-slate-400 italic">
              No manager tasks added yet.
            </div>
          )}
        </div>

        {/* ➕ ADD TASK FOOTER */}
        <div
          className={`p-4 border-t ${
            darkMode
              ? "border-gray-700 bg-gray-800/50"
              : "border-slate-100 bg-slate-50/30"
          }`}
        >
          <div className="flex flex-col gap-3">
            <h4
              className={`text-xs font-bold uppercase tracking-wider ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}
            >
              Add New Task
            </h4>
            <div className="flex gap-3">
              <div className="flex-1">
                <input
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="Enter task description..."
                  className={`
                    w-full px-4 py-2.5 rounded-xl text-sm border outline-none focus:ring-2 transition-all
                    ${
                      darkMode
                        ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:ring-blue-500/50"
                        : "bg-white border-slate-200 text-[#0E1B2E] placeholder-slate-400 focus:ring-blue-500/20 focus:border-blue-400"
                    }
                  `}
                />
              </div>
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value as any)}
                className={`
                  px-4 py-2.5 rounded-xl text-sm font-medium border outline-none focus:ring-2 cursor-pointer
                  ${
                    darkMode
                      ? "bg-gray-700 border-gray-600 text-white focus:ring-blue-500/50"
                      : "bg-white border-slate-200 text-slate-700 focus:ring-blue-500/20"
                  }
                `}
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
              <button
                onClick={addManagerTask}
                disabled={!newTaskTitle.trim()}
                className={`
                  px-5 py-2.5 rounded-xl text-sm font-bold text-white shadow-md transition-all
                  ${
                    !newTaskTitle.trim()
                      ? "bg-slate-300 cursor-not-allowed"
                      : darkMode
                      ? "bg-blue-600 hover:bg-blue-500 hover:shadow-blue-900/20"
                      : "bg-[#0E1B2E] hover:bg-blue-900 hover:shadow-lg hover:scale-105"
                  }
                `}
              >
                <div className="flex items-center gap-1.5">
                  <Plus className="w-4 h-4" />
                  Add
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
