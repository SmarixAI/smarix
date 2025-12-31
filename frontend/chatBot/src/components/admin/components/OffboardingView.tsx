"use client";

import { useState, useEffect } from "react";
import { Loader2, FileText, CheckCircle2, AlertCircle, Info, Users, FileCode, AlertTriangle, ClipboardList, FileCheck, BookOpen, Shield } from "lucide-react";
import { StepStatus } from "./types";
import { getStepIcon } from "./StepCard";

interface OffboardingViewProps {
  darkMode: boolean;
  offboardingStatus: StepStatus;
  offboardingMessage: string;
  offboardingRunning: boolean;
  onRunOffboarding: (selectedSteps: string[], employeeName?: string) => void;
}

interface OffboardingStep {
  id: string;
  name: string;
  description: string;
  icon: any;
  outputFile: string;
  scriptName: string;
}

const steps: OffboardingStep[] = [
  {
    id: "extract_users",
    name: "Extract PR Users",
    description: "Identifies unique PR contributors and assigns employee IDs for tracking",
    icon: Users,
    outputFile: "1employees_with_ids.json",
    scriptName: "1extract_unique_pr_users.py"
  },
  {
    id: "extract_files",
    name: "Extract Changed Files",
    description: "Extracts files changed by each employee and calculates risk scores based on file importance",
    icon: FileCode,
    outputFile: "2employee_changed_files.json",
    scriptName: "2extract_employee_changed_files.py"
  },
  {
    id: "add_criticality",
    name: "Add Criticality Scores",
    description: "Adds criticality scores and commit details to PRs to identify high-priority work",
    icon: AlertTriangle,
    outputFile: "3employee_prs_with_criticality.json",
    scriptName: "3add_criticality_scores.py"
  },
  {
    id: "add_metadata",
    name: "Add Task Metadata",
    description: "Enriches tasks with priority, tags, status, and other metadata for better organization",
    icon: ClipboardList,
    outputFile: "4employee_tasks_with_metadata_finalCallData.json",
    scriptName: "4add_task_metadata.py"
  },
  {
    id: "generate_handovers",
    name: "Generate Handovers",
    description: "Creates handover documentation from tasks, summarizing work for smooth transitions",
    icon: FileCheck,
    outputFile: "5employee_handovers.json",
    scriptName: "5generate_handovers.py"
  },
  {
    id: "generate_documents",
    name: "Generate Documents",
    description: "Generates comprehensive offboarding documents and section preparation guides",
    icon: BookOpen,
    outputFile: "6employee_documents.json",
    scriptName: "6generate_documents.py"
  }
];

export default function OffboardingView({
  darkMode,
  offboardingStatus,
  offboardingMessage,
  offboardingRunning,
  onRunOffboarding,
}: OffboardingViewProps) {
  const [selectedSteps, setSelectedSteps] = useState<string[]>([]);
  const [employeeName, setEmployeeName] = useState<string>("");

  // Initialize with all steps selected
  useEffect(() => {
    if (selectedSteps.length === 0) {
      setSelectedSteps(steps.map(s => s.id));
    }
  }, []);

  const toggleStep = (stepId: string) => {
    setSelectedSteps(prev =>
      prev.includes(stepId)
        ? prev.filter(id => id !== stepId)
        : [...prev, stepId]
    );
  };

  const selectAllSteps = () => {
    setSelectedSteps(steps.map(s => s.id));
  };

  const deselectAllSteps = () => {
    setSelectedSteps([]);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* MAIN CARD */}
      <div
        className={`rounded-xl shadow-lg p-6 ${
          darkMode ? "bg-gray-800" : "bg-white"
        }`}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2
              className={`text-2xl font-semibold mb-2 ${
                darkMode ? "text-white" : "text-slate-900"
              }`}
            >
              Offboarding Data Generation
            </h2>
            <p
              className={`text-sm ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}
            >
              Generate comprehensive offboarding documentation and handover materials
            </p>
          </div>
        </div>

        {/* EMPLOYEE NAME INPUT */}
        <div className="mb-6">
          <div className="mb-4">
            <label
              htmlFor="employee-name"
              className={`block text-sm font-medium mb-2 ${
                darkMode ? "text-gray-300" : "text-slate-700"
              }`}
            >
              Employee Name <span className="text-red-500">*</span>
            </label>
            <p
              className={`text-xs mb-3 ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}
            >
              Enter the employee name to generate offboarding data. The employee must exist in the system.
            </p>
            <input
              id="employee-name"
              type="text"
              value={employeeName}
              onChange={(e) => setEmployeeName(e.target.value)}
              placeholder="e.g., Mastermind-sap"
              required
              disabled={offboardingRunning}
              className={`w-full px-4 py-2.5 rounded-lg border transition-all ${
                darkMode
                  ? employeeName.trim()
                    ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20"
                    : "bg-gray-700 border-red-600 text-white placeholder-gray-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
                  : employeeName.trim()
                  ? "bg-white border-slate-300 text-slate-900 placeholder-slate-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20"
                  : "bg-white border-red-400 text-slate-900 placeholder-slate-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            />
            {!employeeName.trim() && (
              <p
                className={`mt-2 text-xs ${
                  darkMode ? "text-red-400" : "text-red-600"
                }`}
              >
                ⚠️ Employee name is required to generate offboarding data
              </p>
            )}
            {employeeName.trim() && (
              <p
                className={`mt-2 text-xs ${
                  darkMode ? "text-blue-400" : "text-blue-600"
                }`}
              >
                ✓ Data will be generated for "{employeeName.trim()}"
              </p>
            )}
          </div>
        </div>

        {/* STATUS CARD */}
        <div
          className={`p-6 rounded-lg border transition-all mb-6 ${
            offboardingStatus === "completed"
              ? darkMode
                ? "border-green-700 bg-green-900/20"
                : "border-emerald-200 bg-emerald-50"
              : offboardingStatus === "running"
              ? darkMode
                ? "border-blue-700 bg-blue-900/20 ring-2 ring-blue-800"
                : "border-sky-200 bg-sky-50 ring-2 ring-sky-200"
              : offboardingStatus === "error"
              ? darkMode
                ? "border-red-700 bg-red-900/20"
                : "border-rose-200 bg-rose-50"
              : darkMode
              ? "border-gray-700 bg-gray-800"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {getStepIcon(offboardingStatus)}
              <div>
                <h3
                  className={`text-lg font-semibold ${
                    darkMode ? "text-white" : "text-slate-900"
                  }`}
                >
                  Offboarding Generation Status
                </h3>
                <p
                  className={`text-sm ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`}
                >
                  {offboardingStatus === "pending" && "Ready to generate offboarding data"}
                  {offboardingStatus === "running" && "Generating offboarding documentation..."}
                  {offboardingStatus === "completed" && "Offboarding data generated successfully"}
                  {offboardingStatus === "error" && "Generation failed"}
                </p>
              </div>
            </div>

            <button
              onClick={() => onRunOffboarding(selectedSteps, employeeName.trim())}
              disabled={offboardingRunning || selectedSteps.length === 0 || !employeeName.trim()}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                offboardingRunning || selectedSteps.length === 0 || !employeeName.trim()
                  ? darkMode
                    ? "bg-gray-600 cursor-not-allowed"
                    : "bg-slate-200 text-slate-500 cursor-not-allowed"
                  : "bg-rose-600 hover:bg-rose-700 text-white"
              } shadow-md hover:shadow-lg disabled:shadow-none`}
            >
              {offboardingRunning ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </span>
              ) : (
                `Generate Offboarding Data`
              )}
            </button>
          </div>

          {/* MESSAGE */}
          {offboardingMessage && (
            <div
              className={`mt-4 p-3 rounded-lg text-sm ${
                offboardingStatus === "completed"
                  ? darkMode
                    ? "bg-green-900/30 text-green-300"
                    : "bg-emerald-100 text-emerald-700"
                  : offboardingStatus === "error"
                  ? darkMode
                    ? "bg-red-900/30 text-red-300"
                    : "bg-rose-100 text-rose-700"
                  : darkMode
                  ? "bg-blue-900/30 text-blue-300"
                  : "bg-sky-100 text-sky-700"
              }`}
            >
              {offboardingMessage}
            </div>
          )}
        </div>

      </div>

      {/* OUTPUT FILES SECTION */}
      {offboardingStatus === "completed" && (
        <div
          className={`rounded-xl shadow-lg p-6 ${
            darkMode ? "bg-gray-800" : "bg-white"
          }`}
        >
          <h3
            className={`text-xl font-semibold mb-4 ${
              darkMode ? "text-white" : "text-slate-900"
            }`}
          >
            Generated Files
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {steps
              .filter(s => selectedSteps.includes(s.id))
              .map((step, index) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.id}
                    className={`p-3 rounded-lg border ${
                      darkMode
                        ? "bg-gray-700/50 border-gray-600"
                        : "bg-slate-50 border-slate-200"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className={`w-4 h-4 ${
                        darkMode ? "text-gray-400" : "text-slate-600"
                      }`} />
                      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                        darkMode
                          ? "bg-gray-700 text-gray-300"
                          : "bg-slate-200 text-slate-600"
                      }`}>
                        {index + 1}
                      </span>
                      <span className={`text-sm font-medium ${
                        darkMode ? "text-white" : "text-slate-900"
                      }`}>
                        {step.name}
                      </span>
                    </div>
                    <p className={`text-xs ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}>
                      {step.outputFile}
                    </p>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

