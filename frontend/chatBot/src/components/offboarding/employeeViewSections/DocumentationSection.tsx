"use client";

import { useEffect, useState, useRef } from "react";
import {
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Brain,
  HelpCircle,
  Upload,
  Loader2,
  ShieldCheck,
  AlertCircle,
  FileCheck,
  Info,
  Target,
  RefreshCcw,
  ArrowUpCircle,
  Download,
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
};

type TaskAIStatus = {
  status: "idle" | "analyzing" | "completed";
  progress: number;
  score: number | null;
  fileName?: string;
  report?: Record<string, unknown>;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
  initialTasksData?: { employees?: any[] } | null;
  onTasksUpdated?: () => void;
};

const getPriorityStyles = (priority: Task["priority"]): string => {
  return priority === "High"
    ? "bg-red-50 text-red-700 border-red-200"
    : priority === "Medium"
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : "bg-emerald-50 text-emerald-700 border-emerald-200";
};

export default function EmployeeDocumentationSection({
  employeeId,
  darkMode = false,
  initialTasksData,
  onTasksUpdated,
}: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(
    new Set(),
  );
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(
    new Set(),
  );

  const [taskAIStates, setTaskAIStates] = useState<
    Record<string, TaskAIStatus>
  >({});
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [activeFilter, setActiveFilter] = useState<
    "all" | "high" | "medium" | "low"
  >("all");

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === "all") return true;
    return task.priority.toLowerCase() === activeFilter;
  });

  const hasParentData = initialTasksData !== undefined;

  useEffect(() => {
    const applyData = (data: { employees?: any[] } | null) => {
      if (!data?.employees?.length) {
        setTasks([]);
        setTaskAIStates({});
        setLoading(false);
        return;
      }
      const employee =
        data.employees.find(
          (e: any) => String(e.employeeId) === String(employeeId),
        ) ?? data.employees[0];
      const docTasks = (employee?.tasks?.ai ?? [])
        .filter((t: any) => t.id.startsWith("DOC"))
        .map((t: any) => ({ ...t, tags: t.tags || ["Manual"] }));
      setTasks(docTasks);
      const initialStates: Record<string, TaskAIStatus> = {};
      docTasks.forEach((t: Task) => {
        initialStates[t.id] = { status: "idle", progress: 0, score: null };
      });
      setTaskAIStates(initialStates);
      docTasks.forEach((t: Task) => {
        fetch(
          `/api/offboarding/aianalytics?employeeId=${encodeURIComponent(employeeId)}&taskId=${encodeURIComponent(t.id)}`
        )
          .then((r) => (r.ok ? r.json() : null))
          .then((report) => {
            if (report) {
              setTaskAIStates((prev) => ({
                ...prev,
                [t.id]: {
                  status: "completed",
                  progress: 100,
                  score: report.score ?? null,
                  fileName: "Document uploaded",
                  report,
                },
              }));
            }
          })
          .catch(() => {});
      });
      setLoading(false);
    };

    if (hasParentData) {
      if (initialTasksData == null) {
        setLoading(true);
        setTasks([]);
        setTaskAIStates({});
        return;
      }
      applyData(initialTasksData);
      return;
    }

    setLoading(true);
    fetch(`/api/offboarding/tasks?employeeId=${encodeURIComponent(employeeId)}`)
      .then((res) => res.json())
      .then((data) => applyData(data))
      .catch((error) => {
        console.error(error);
        setLoading(false);
      });
  }, [employeeId, hasParentData, initialTasksData]);

  const handleFileUpload = async (
    taskId: string,
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".txt")) {
      alert("Only .txt files allowed");
      return;
    }

    setTaskAIStates((prev) => ({
      ...prev,
      [taskId]: {
        status: "analyzing",
        progress: 0,
        score: null,
        fileName: file.name,
      },
    }));

    const formDataBackend = new FormData();
    formDataBackend.append("employeeId", employeeId);
    formDataBackend.append("documentId", taskId);
    formDataBackend.append("file", file);

    try {
      // 1) Upload .txt to S3: Offboarding/{employeeId}/upload/{taskId}.txt
      const uploadForm = new FormData();
      uploadForm.append("employeeId", employeeId);
      uploadForm.append("taskId", taskId);
      uploadForm.append("file", file);
      const uploadRes = await fetch("/api/offboarding/upload", {
        method: "POST",
        body: uploadForm,
      });
      if (!uploadRes.ok) {
        const errData = await uploadRes.json().catch(() => ({}));
        throw new Error(errData.error || "Upload to S3 failed");
      }

      // 2) Run AI analysis (backend)
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/analyze-document`,
        {
          method: "POST",
          body: formDataBackend,
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "AI failed");
      }

      // 3) Store AI report in S3: Offboarding/{employeeId}/aianalytics/{taskId}.json
      const reportRes = await fetch("/api/offboarding/aianalytics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employeeId,
          taskId,
          report: data,
        }),
      });
      if (!reportRes.ok) {
        console.warn("AI report save to S3 failed", await reportRes.text());
      }

      setTaskAIStates((prev) => ({
        ...prev,
        [taskId]: {
          status: "completed",
          progress: 100,
          score: data.score,
          fileName: file.name,
          report: data,
        },
      }));
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "AI analysis failed");
      setTaskAIStates((prev) => ({
        ...prev,
        [taskId]: {
          status: "idle",
          progress: 0,
          score: null,
        },
      }));
    }

    e.target.value = "";
  };


  const toggleTaskDetails = (taskId: string) => {
    setExpandedTaskIds((prev) => {
      const newSet = new Set(prev);
      newSet.has(taskId) ? newSet.delete(taskId) : newSet.add(taskId);
      return newSet;
    });
  };

  if (loading)
    return (
      <Loader
        darkMode={false}
        message="Analyzing documentation requirements..."
        size="md"
      />
    );

  return (
    <div className="w-full h-full flex flex-col pt-6 pb-0">
      {/* Main Container - Ensuring it fills height and width without gaps */}
      <div className="flex-1 w-full rounded-[2rem] border-2 border-slate-200 shadow-lg bg-white/70 backdrop-blur-sm flex flex-col min-h-0 overflow-hidden">
        {/* Header */}
        <div className="px-8 py-6 border-b-2 border-slate-200 bg-slate-50/50 flex justify-between items-center">
          <div>
            <h2
              className={`${inter.className} text-2xl font-extrabold text-[#0E1B2E] tracking-tight`}
            >
              Handover Documentation
            </h2>
            <p className="text-sm text-slate-500 font-medium">
              Systematic verification of knowledge transfer assets
            </p>
          </div>
          <div className="flex gap-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
            {["all", "high", "medium", "low"].map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f as any)}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all uppercase tracking-widest ${activeFilter === f
                    ? "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white shadow-md"
                    : "text-slate-400 hover:text-slate-600"
                  }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Task List - min-h-0 and flex-1 allows it to scroll correctly without extra bottom padding */}
        <div className="flex-1 overflow-y-auto divide-y-2 divide-slate-200">
          {filteredTasks.map((task) => {
            const isDone = completedTaskIds.has(task.id);
            const isExpanded = expandedTaskIds.has(task.id);
            const ai = taskAIStates[task.id] || {
              status: "idle",
              progress: 0,
              score: null,
            };

            return (
              <div
                key={task.id}
                className={`transition-all duration-300 ${isDone ? "bg-emerald-50/20" : isExpanded ? "bg-slate-50/50" : ""}`}
              >
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
                          <FileText className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <h4
                          className={`${inter.className} text-base font-bold text-[#0E1B2E] flex items-center gap-3`}
                        >
                          {task.title || task.id}
                        </h4>
                        <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wide mt-0.5">
                          ID: {task.id}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* Show this badge if the task is finished */}
                      {isDone && (
                        <>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(task.priority)}`}
                          >
                            {task.priority}
                          </span>
                          <span
                            className={`${inter.className} flex items-center gap-1.5 text-xs font-bold text-green-700 bg-green-50 px-3 py-2 rounded-xl border-2 border-green-200 animate-in fade-in zoom-in-95`}
                          >
                            <CheckCircle className="w-4 h-4" />
                            Documented
                          </span>
                        </>
                      )}
                      {ai.status === "idle" && !isDone && (
                        <>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(task.priority)}`}
                          >
                            {task.priority}
                          </span>
                          <button
                            onClick={() =>
                              fileInputRefs.current[task.id]?.click()
                            }
                            className={`${inter.className} flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-white transition-all bg-gradient-to-r from-[#0E1B2E] to-blue-900 hover:shadow-lg shadow-blue-900/10 active:scale-95`}
                          >
                            <Upload className="w-3.5 h-3.5" />
                            <span>Upload File</span>
                          </button>
                        </>
                      )}

                      {ai.status === "analyzing" && (
                        <>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(task.priority)}`}
                          >
                            {task.priority}
                          </span>
                          <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-2xl border border-blue-100 shadow-sm">
                            <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                            <span
                              className={`${jetbrainsMono.className} text-[10px] font-bold text-blue-600`}
                            >
                              {ai.progress}% Audit
                            </span>
                          </div>
                        </>
                      )}

                      {ai.status === "completed" && !isDone && (
                        <>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] w-15 h-[18px] text-[12px] mr-5 flex items-center justify-center font-black border tracking-tighter ${getPriorityStyles(task.priority)}`}
                          >
                            {task.priority}
                          </span>
                          <div className="flex items-center gap-3 animate-in zoom-in-95 duration-300">
                            <div className="bg-emerald-50 px-4 py-2 rounded-xl border border-emerald-200 flex items-center gap-2">
                              <ShieldCheck className="w-4 h-4 text-emerald-600" />
                              <span className="text-xs font-black text-emerald-700">
                                {ai.score}% Compliance
                              </span>
                            </div>
                            <button
                              onClick={() =>
                                setCompletedTaskIds((prev) =>
                                  new Set(prev).add(task.id),
                                )
                              }
                              className={`${inter.className} flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white transition-all bg-gradient-to-r from-green-600 to-emerald-700 hover:shadow-lg hover:shadow-green-900/20 active:scale-95`}
                            >
                              <CheckCircle className="w-4 h-4" />
                              <span>Mark Complete</span>
                            </button>
                          </div>
                        </>
                      )}

                      <input
                        type="file"
                        ref={(el) => {
                          fileInputRefs.current[task.id] = el;
                        }}
                        onChange={(e) => handleFileUpload(task.id, e)}
                        className="hidden"
                      />
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

                  {/* BODY CONTENT - Professional borders and standardized font */}
                  {isExpanded && (
                    <div className="mt-6 mb-2 animate-in fade-in slide-in-from-top-4 duration-300">
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 rounded-2xl bg-white border-2 border-slate-200 shadow-lg overflow-hidden">
                        <div className="lg:col-span-7 p-8 space-y-8 border-r-2 border-slate-200">
                          <section>
                            <div className="flex items-center gap-2 mb-3 text-slate-400">
                              <Info className="w-4 h-4" />
                              <h5 className="text-[10px] font-black uppercase tracking-widest">
                                Requirement Overview
                              </h5>
                            </div>
                            <p className="text-sm text-slate-600 leading-relaxed font-medium">
                              {task.description
                                ?.replace(/\*\*/g, "")
                                .replace(/#{1,6}\s*/g, "")}
                            </p>
                          </section>

                          <section className="bg-slate-50/50 p-6 rounded-xl border border-slate-200">
                            <div className="flex items-center gap-2 mb-4 text-blue-600">
                              <Target className="w-4 h-4" />
                              <h5 className="text-[10px] font-bold uppercase tracking-widest">
                                Points to Cover
                              </h5>
                            </div>
                            <ul className="space-y-3">
                              {task.questions?.map((q, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-[#0E1B2E] font-bold flex items-start gap-3"
                                >
                                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                                  <span>{q}</span>
                                </li>
                              ))}
                            </ul>
                          </section>
                        </div>

                        <div className="lg:col-span-5 p-8 bg-[#FBFDFF] flex flex-col justify-center">
                          <div
                            className={`h-full rounded-2xl p-6 border flex flex-col transition-all duration-500 ${ai.status === "completed" ? "bg-white border-emerald-200 shadow-md" : "bg-slate-50/50 border-dashed border-slate-300"}`}
                          >
                            {ai.status === "completed" ? (
                              <div className="space-y-5">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <Brain className="w-5 h-5 text-indigo-600" />
                                    <span className="text-[10px] font-black uppercase text-slate-800 tracking-tight">
                                      AI Compliance Report
                                    </span>
                                  </div>
                                  <span className="text-2xl font-black text-emerald-600 tabular-nums">
                                    {ai.score}%
                                  </span>
                                </div>

                                <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100 flex gap-3 items-center">
                                  <FileCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                  <p className="text-[11px] font-bold text-emerald-800 truncate">
                                    {ai.fileName ?? "Document uploaded"}
                                  </p>
                                </div>

                                <a
                                  href={`/api/offboarding/upload?employeeId=${encodeURIComponent(employeeId)}&taskId=${encodeURIComponent(task.id)}`}
                                  download={`${task.id}.txt`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="w-full flex items-center justify-center gap-2 py-2 border border-slate-200 rounded-lg text-[10px] font-bold text-slate-600 hover:bg-slate-50 hover:text-[#0E1B2E] transition-all uppercase tracking-widest"
                                >
                                  <Download className="w-3 h-3" /> Download uploaded file
                                </a>

                                <div className="space-y-2.5 py-2">
                                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <ArrowUpCircle className="w-3 h-3" />{" "}
                                    Potential Improvements
                                  </p>
                                  <div className="space-y-2">
                                    {ai.report?.improvements?.map((item, idx) => (
                                      <div key={idx} className="flex items-center gap-2 text-[10px] text-slate-600 font-bold bg-slate-50 p-2 rounded-lg border border-slate-100">
                                        <div className="w-1 h-1 rounded-full bg-slate-300" />
                                        {item}
                                      </div>
                                    ))}                              
                                  </div>
                                </div>

                                <button
                                  onClick={() =>
                                    fileInputRefs.current[task.id]?.click()
                                  }
                                  className="w-full flex items-center justify-center gap-2 py-2 border border-slate-200 rounded-lg text-[10px] font-bold text-slate-500 hover:bg-slate-50 hover:text-[#0E1B2E] transition-all uppercase tracking-widest"
                                >
                                  <RefreshCcw className="w-3 h-3" /> Re-upload &
                                  Re-Audit
                                </button>
                              </div>
                            ) : (
                              <div className="text-center space-y-3 py-6">
                                <div className="w-12 h-12 rounded-full bg-white border border-slate-200 mx-auto flex items-center justify-center shadow-sm">
                                  <Upload className="w-6 h-6 text-slate-200" />
                                </div>
                                <div>
                                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                                    Awaiting Analysis
                                  </p>
                                  <p className="text-[10px] text-slate-300 mt-1 max-w-[180px] mx-auto font-medium">
                                    Neural verification will initiate upon file
                                    upload.
                                  </p>
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