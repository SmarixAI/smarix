"use client";

import { useEffect, useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  ExternalLink,
  User,
  Calendar,
  Clock,
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

type Handover = {
  id: string;
  item: string;
  currentOwner: string;
  newOwner?: string;
  priority: "High" | "Medium" | "Low";
  status: "Pending" | "In Progress" | "Completed";
  ktType: string[];
  lastUpdated: string;
  description?: string;
  questions?: string[];
  reference?: string;
  suggested_recipient?: string;
  suggested_recipient_reason?: string;
};

type HandoverSectionProps = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= COMPONENT ================= */

export default function HandoverSection({
  employeeId,
  darkMode = false,
}: HandoverSectionProps) {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [updateCounter, setUpdateCounter] = useState(0); // Force re-render
  const [priorityFilter, setPriorityFilter] = useState<
    "All" | "High" | "Medium" | "Low"
  >("All");
  const [loading, setLoading] = useState(true);

  // local UI-only state for scheduling
  const [schedule, setSchedule] = useState<
    Record<string, { owner: string; date: string; time: string }>
  >({});

  // Expanded handover IDs
  const [expandedHandoverIds, setExpandedHandoverIds] = useState<Set<string>>(
    new Set()
  );

  /* ================= LOAD HANDOVERS ================= */

  useEffect(() => {
    // Clear state when employeeId changes
    setHandovers([]);
    setUpdateCounter(0); // Reset update counter
    setLoading(true);

    const fetchData = async () => {
      try {
        const response = await fetch("/api/offboarding/handovers");
        if (!response.ok) {
          console.error("Failed to fetch handovers data");
          setLoading(false);
          return;
        }
        const data = await response.json();

        if (!data?.employees?.length) {
          console.log(
            "Manager Handover - No employees found in handovers data"
          );
          setLoading(false);
          return;
        }

        console.log("Manager Handover - Looking for employeeId:", employeeId);
        console.log(
          "Manager Handover - Available employeeIds:",
          data.employees.map((e: any) => e.employeeId || e.employee_id)
        );

        // Try multiple matching strategies
        let employee = data.employees.find(
          (e: any) =>
            e.employeeId === employeeId ||
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId) ||
            e.name === employeeId ||
            e.employee_name === employeeId
        );

        if (!employee) {
          console.log(
            "Manager Handover - Employee not found, using first employee"
          );
          employee = data.employees[0];
        }

        console.log(
          "Manager Handover - Found employee:",
          employee
            ? {
                employeeId: employee.employeeId || employee.employee_id,
                name: employee.name,
              }
            : "NOT FOUND"
        );
        console.log(
          "Manager Handover - Employee handovers:",
          employee?.handovers
        );

        // Set handovers if employee found (removed strict check to allow fallback)
        if (employee) {
          setHandovers(employee.handovers ?? []);
        }
      } catch (error) {
        console.error("Error fetching handovers data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY (NEW) ================= */

  const summary = useMemo(() => {
    const total = handovers.length;
    const completed = handovers.filter((h) => h.status === "Completed").length;
    const inProgress = handovers.filter(
      (h) => h.status === "In Progress"
    ).length;
    const pending = handovers.filter((h) => h.status === "Pending").length;
    const assigned = handovers.filter(
      (h) => h.newOwner && h.newOwner.trim().length > 0
    ).length;
    const yetToAssign = total - assigned;

    return {
      total,
      completed,
      inProgress,
      pending,
      assigned,
      yetToAssign,
    };
  }, [handovers]);

  // Filter handovers based on priority
  const filteredHandovers = useMemo(() => {
    if (priorityFilter === "All") return handovers;
    return handovers.filter((h) => h.priority === priorityFilter);
  }, [handovers, priorityFilter]);

  /* ================= UPDATE HELPERS ================= */

  const updateHandover = async (id: string, updates: Partial<Handover>) => {
    // Store old priority for potential revert
    const oldPriority = updates.priority
      ? handovers.find((h) => h.id === id)?.priority
      : undefined;

    // Update local state immediately using functional form
    setHandovers((prev) =>
      prev.map((h) => (h.id === id ? { ...h, ...updates } : h))
    );
    // Force re-render
    if (updates.priority) {
      setUpdateCounter((prev) => prev + 1);
    }

    // If priority is being updated, persist to backend
    if (updates.priority) {
      try {
        const response = await fetch("/api/offboarding/handovers", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            employeeId: employeeId,
            handoverId: id,
            priority: updates.priority,
          }),
        });

        if (!response.ok) {
          console.error("Failed to update handover priority");
          // Revert on error using functional form
          if (oldPriority) {
            setHandovers((prev) =>
              prev.map((h) =>
                h.id === id ? { ...h, priority: oldPriority } : h
              )
            );
          }
        }
      } catch (error) {
        console.error("Error updating handover priority:", error);
        // Revert on error using functional form
        if (oldPriority) {
          setHandovers((prev) =>
            prev.map((h) => (h.id === id ? { ...h, priority: oldPriority } : h))
          );
        }
      }
    }
  };

  const updateSchedule = (
    id: string,
    key: "owner" | "date" | "time",
    value: string
  ) => {
    setSchedule((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [key]: value,
      },
    }));
  };

  const scheduleMeeting = (h: Handover) => {
    const s = schedule[h.id];
    console.log("📅 Scheduling KT meeting", {
      item: h.item,
      from: h.currentOwner,
      to: s?.owner || h.newOwner,
      date: s?.date,
      time: s?.time,
    });

    alert("KT Meeting scheduled (mock)");
  };

  const getPriorityStyles = (
    priority: Handover["priority"],
    darkMode: boolean
  ): string => {
    if (darkMode) {
      return priority === "High"
        ? "bg-red-900/40 text-red-200 border-red-800 focus:ring-red-400"
        : priority === "Medium"
        ? "bg-amber-900/40 text-amber-200 border-amber-800 focus:ring-amber-400"
        : "bg-emerald-900/40 text-emerald-200 border-emerald-800 focus:ring-green-400";
    }
    return priority === "High"
      ? "bg-red-50 text-red-700 border-red-200 focus:ring-red-400"
      : priority === "Medium"
      ? "bg-amber-50 text-amber-700 border-amber-200 focus:ring-amber-400"
      : "bg-emerald-50 text-emerald-700 border-emerald-200 focus:ring-green-400";
  };

  /* ================= UI ================= */

  if (loading) {
    return (
      <Loader darkMode={darkMode} message="Loading handovers..." size="md" />
    );
  }

  return (
    <div className={`space-y-4 p-1 ${inter.className}`}>
      {/* ================= FILTERS ================= */}
      <div
        className={`rounded-xl border px-4 py-3 flex items-center gap-4 transition-colors ${
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
      </div>

      {/* ================= SECTION TITLE ================= */}
      <h2
        className={`text-xs font-bold uppercase tracking-wider mb-2 px-1 ${
          darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
        }`}
      >
        Feature-Level Handovers ({filteredHandovers.length})
      </h2>

      {/* ================= HANDOVER LIST ================= */}
      <div className="space-y-3">
        {filteredHandovers.length > 0 ? (
          filteredHandovers.map((h) => {
            const isExpanded = expandedHandoverIds.has(h.id);
            const hasDetails =
              h.description ||
              h.questions?.length ||
              h.reference ||
              h.suggested_recipient_reason;

            return (
              <div
                key={h.id}
                className={`rounded-xl border overflow-hidden transition-all duration-300 ${
                  darkMode
                    ? "border-gray-700 bg-gray-800/30"
                    : "border-slate-200 bg-white shadow-sm hover:shadow-md"
                }`}
              >
                {/* TOP ROW */}
                <div
                  className={`flex items-start justify-between gap-4 p-4 cursor-pointer transition-colors ${
                    hasDetails
                      ? darkMode
                        ? "hover:bg-gray-800/70"
                        : "hover:bg-slate-50"
                      : ""
                  } ${
                    isExpanded
                      ? darkMode
                        ? "bg-gray-800/30"
                        : "bg-slate-50/50"
                      : ""
                  }`}
                  onClick={() =>
                    hasDetails &&
                    setExpandedHandoverIds((prev) => {
                      const newSet = new Set(prev);
                      if (newSet.has(h.id)) {
                        newSet.delete(h.id);
                      } else {
                        newSet.add(h.id);
                      }
                      return newSet;
                    })
                  }
                >
                  <div className="flex-1 flex items-start gap-3">
                    {hasDetails && (
                      <div className="mt-0.5 text-slate-400">
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </div>
                    )}
                    <div>
                      <p
                        className={`text-sm font-semibold ${
                          darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                        }`}
                      >
                        {h.item}
                      </p>
                      <div
                        className={`text-xs mt-1 flex items-center gap-2 ${
                          darkMode ? "text-gray-400" : "text-slate-500"
                        }`}
                      >
                        <span>{h.currentOwner}</span>
                        <span className="text-slate-300">→</span>
                        <span
                          className={`font-medium px-1.5 py-0.5 rounded ${
                            darkMode
                              ? "bg-gray-700 text-gray-200"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {h.newOwner || "Unassigned"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <span
                    className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border ${
                      h.priority === "High"
                        ? darkMode
                          ? "bg-red-900/40 text-red-200 border-red-800"
                          : "bg-red-50 text-red-700 border-red-100"
                        : h.priority === "Medium"
                        ? darkMode
                          ? "bg-amber-900/40 text-amber-200 border-amber-800"
                          : "bg-amber-50 text-amber-700 border-amber-100"
                        : darkMode
                        ? "bg-emerald-900/40 text-emerald-200 border-emerald-800"
                        : "bg-emerald-50 text-emerald-700 border-emerald-100"
                    }`}
                  >
                    {h.priority}
                  </span>
                </div>

                {/* META INFO */}
                <div
                  className={`px-4 pb-3 flex flex-wrap gap-4 text-xs ${
                    darkMode ? "text-gray-400" : "text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-slate-400">
                      Status:
                    </span>
                    <span
                      className={`font-semibold ${
                        h.status === "Pending"
                          ? darkMode
                            ? "text-red-400"
                            : "text-red-600"
                          : h.status === "In Progress"
                          ? darkMode
                            ? "text-amber-400"
                            : "text-amber-600"
                          : darkMode
                          ? "text-emerald-400"
                          : "text-emerald-600"
                      }`}
                    >
                      {h.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-slate-400">Type:</span>
                    <span>{h.ktType.join(", ")}</span>
                  </div>

                  <div className="flex items-center gap-1.5 ml-auto">
                    <Clock className="w-3 h-3" />
                    <span>Updated {h.lastUpdated}</span>
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
                      {h.description && (
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
                            {h.description
                              .replace(/\*\*/g, "")
                              .replace(/#{1,6}\s*/g, "")}
                          </div>
                        </div>
                      )}

                      {/* QUESTIONS */}
                      {h.questions && h.questions.length > 0 && (
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
                              Questions ({h.questions.length})
                            </h4>
                          </div>
                          <ul className="space-y-1">
                            {h.questions.map((q, idx) => (
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

                      {/* REFERENCE */}
                      {h.reference && (
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <ExternalLink
                              className={`w-3.5 h-3.5 ${
                                darkMode ? "text-gray-400" : "text-slate-500"
                              }`}
                            />
                            <h4
                              className={`text-xs font-bold uppercase tracking-wider ${
                                darkMode ? "text-gray-300" : "text-slate-700"
                              }`}
                            >
                              References
                            </h4>
                          </div>
                          <div
                            className={`text-xs ${
                              darkMode ? "text-gray-400" : "text-slate-600"
                            }`}
                          >
                            {h.reference.split(", ").map((ref, idx) => (
                              <div
                                key={idx}
                                className="font-mono bg-slate-100 dark:bg-gray-800 px-2 py-1 rounded w-fit mb-1"
                              >
                                {ref}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* SUGGESTED RECIPIENT */}
                      {h.suggested_recipient && (
                        <div
                          className={`p-3 rounded-lg border ${
                            darkMode
                              ? "bg-blue-900/20 border-blue-800"
                              : "bg-blue-50 border-blue-100"
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <User
                              className={`w-3.5 h-3.5 ${
                                darkMode ? "text-blue-300" : "text-blue-600"
                              }`}
                            />
                            <h4
                              className={`text-xs font-bold uppercase tracking-wider ${
                                darkMode ? "text-blue-200" : "text-blue-800"
                              }`}
                            >
                              Suggested Recipient
                            </h4>
                          </div>
                          <div
                            className={`text-xs ${
                              darkMode ? "text-blue-300" : "text-blue-700"
                            }`}
                          >
                            <div className="font-semibold">
                              {h.suggested_recipient}
                            </div>
                            {h.suggested_recipient_reason && (
                              <div className="mt-1 opacity-80">
                                {h.suggested_recipient_reason}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* ================= HANDOVER CONTROLS ================= */}
                <div
                  className={`p-3 border-t bg-slate-50/50 ${
                    darkMode
                      ? "border-gray-700 bg-gray-800/30"
                      : "border-slate-100"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Priority Select */}
                    <div className="relative group">
                      <select
                        key={`${h.id}-${h.priority}-${updateCounter}`}
                        value={h.priority}
                        onChange={(e) =>
                          updateHandover(h.id, {
                            priority: e.target.value as Handover["priority"],
                          })
                        }
                        className={`
                        appearance-none pl-3 pr-8 py-1.5 rounded-lg text-xs font-bold border cursor-pointer outline-none focus:ring-2
                        transition-all duration-200
                        ${getPriorityStyles(h.priority, darkMode)}
                      `}
                      >
                        <option value="High">High Priority</option>
                        <option value="Medium">Medium Priority</option>
                        <option value="Low">Low Priority</option>
                      </select>
                      <ChevronDown
                        className={`w-3 h-3 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none opacity-50 ${
                          h.priority === "High"
                            ? darkMode
                              ? "text-red-200"
                              : "text-red-700"
                            : h.priority === "Medium"
                            ? darkMode
                              ? "text-amber-200"
                              : "text-amber-800"
                            : darkMode
                            ? "text-emerald-200"
                            : "text-emerald-700"
                        }`}
                      />
                    </div>

                    <div className="h-4 w-px bg-slate-200 dark:bg-gray-700 mx-1"></div>

                    {/* Owner Select */}
                    <select
                      value={schedule[h.id]?.owner || h.newOwner || ""}
                      onChange={(e) =>
                        updateSchedule(h.id, "owner", e.target.value)
                      }
                      className={`
                      px-3 py-1.5 rounded-lg text-xs font-medium border outline-none focus:ring-2 cursor-pointer
                      ${
                        darkMode
                          ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                          : "border-slate-200 bg-white text-slate-700 focus:ring-blue-500/20"
                      }
                    `}
                    >
                      <option value="">Select New Owner</option>
                      <option value="Ankit Sharma">Ankit Sharma</option>
                      <option value="Neha Gupta">Neha Gupta</option>
                      <option value="Rohit Mehta">Rohit Mehta</option>
                    </select>

                    {/* Date Input */}
                    <div className="relative">
                      <input
                        type="date"
                        value={schedule[h.id]?.date || ""}
                        onChange={(e) =>
                          updateSchedule(h.id, "date", e.target.value)
                        }
                        className={`
                        pl-8 pr-2 py-1.5 rounded-lg text-xs border outline-none focus:ring-2
                        ${
                          darkMode
                            ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                            : "border-slate-200 bg-white text-slate-700 focus:ring-blue-500/20"
                        }
                      `}
                      />
                      <Calendar className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                    </div>

                    {/* Time Input */}
                    <div className="relative">
                      <input
                        type="time"
                        value={schedule[h.id]?.time || ""}
                        onChange={(e) =>
                          updateSchedule(h.id, "time", e.target.value)
                        }
                        className={`
                        pl-8 pr-2 py-1.5 rounded-lg text-xs border outline-none focus:ring-2
                        ${
                          darkMode
                            ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                            : "border-slate-200 bg-white text-slate-700 focus:ring-blue-500/20"
                        }
                      `}
                      />
                      <Clock className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                    </div>

                    {/* Schedule Button */}
                    <button
                      onClick={() => scheduleMeeting(h)}
                      className={`
                      ml-auto px-4 py-1.5 rounded-lg text-xs font-bold text-white shadow-md transition-all
                      ${
                        darkMode
                          ? "bg-blue-600 hover:bg-blue-500 hover:shadow-blue-900/20"
                          : "bg-[#0E1B2E] hover:bg-blue-900 hover:shadow-lg hover:scale-105"
                      }
                    `}
                    >
                      Schedule KT
                    </button>
                  </div>
                </div>
              </div>
            );
          })
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
              {handovers.length === 0
                ? "No handover items for this employee."
                : "No handovers match the current filter."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
