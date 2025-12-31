"use client";

import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { Step, StepStatus } from "./types";

interface StepCardProps {
  step: Step;
  index: number;
  totalSteps: number;
  darkMode: boolean;
  executionMode: "full" | "step-by-step";
  isRunning: boolean;
  organization: string;
  repoName: string;
  onRunStep: (stepId: string) => void;
}

/* ================= ICON ================= */

export function getStepIcon(status: StepStatus) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="w-6 h-6 text-green-500" />;
    case "running":
      return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
    case "error":
      return <XCircle className="w-6 h-6 text-red-500" />;
    default:
      return <Circle className="w-6 h-6 text-blue-300" />;
  }
}

/* ================= COLOR MAP (NO dark:) ================= */

function getCardClasses(status: StepStatus, darkMode: boolean) {
  if (darkMode) {
    // DARK MODE (intentional dark surface)
    switch (status) {
      case "completed":
        return "bg-green-900/20 border-green-700";
      case "running":
        return "bg-blue-900/20 border-blue-700 ring-2 ring-blue-800";
      case "error":
        return "bg-red-900/20 border-red-700";
      default:
        return "bg-gray-800 border-gray-700";
    }
  }

  // ✅ LIGHT MODE (PURE LIGHT — matches History)
  switch (status) {
    case "completed":
      return "bg-green-50 border-green-200";
    case "running":
      return "bg-blue-50 border-blue-200 ring-2 ring-blue-100";
    case "error":
      return "bg-red-50 border-red-200";
    default:
      return "bg-white border-slate-200";
  }
}

/* ================= COMPONENT ================= */

export default function StepCard({
  step,
  index,
  totalSteps,
  darkMode,
  executionMode,
  isRunning,
  organization,
  repoName,
  onRunStep,
}: StepCardProps) {
  return (
    <div>
      {/* STEP CARD */}
      <div
        className={`border rounded-lg p-4 transition-all duration-300 ${getCardClasses(
          step.status,
          darkMode
        )}`}
      >
        <div className="flex items-start gap-4">
          {/* ICON */}
          <div className="flex-shrink-0 mt-1">
            {getStepIcon(step.status)}
          </div>

          {/* CONTENT */}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h3 className={`text-lg font-semibold ${
                darkMode ? "text-white" : "text-slate-900"
              }`}>
                {step.name}
              </h3>
              <span className={`text-xs font-medium ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}>
                Step {index + 1} of {totalSteps}
              </span>
            </div>

            <p className={`text-sm mb-2 ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>
              {step.description}
            </p>

            {step.message && (
              <div
                className={`text-sm mt-2 p-3 rounded border ${
                  step.status === "error"
                    ? darkMode
                      ? "bg-red-900/30 border-red-800 text-red-400"
                      : "bg-red-100 border-red-200 text-red-700"
                    : step.status === "completed"
                    ? darkMode
                      ? "bg-green-900/30 border-green-800 text-green-400"
                      : "bg-green-100 border-green-200 text-green-700"
                    : darkMode
                      ? "bg-blue-900/30 border-blue-800 text-blue-400"
                      : "bg-blue-100 border-blue-200 text-blue-700"
                }`}
              >
                {step.message}
              </div>
            )}

            {executionMode === "step-by-step" && step.status !== "running" && (
              <button
                onClick={() => onRunStep(step.id)}
                disabled={
                  isRunning ||
                  !organization.trim() ||
                  !repoName.trim() ||
                  step.status === "completed"
                }
                className={`mt-3 px-4 py-2 rounded text-sm font-medium transition-all ${
                  step.status === "completed"
                    ? darkMode
                      ? "bg-gray-700 text-gray-400"
                      : "bg-slate-100 text-slate-500"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                }`}
              >
                {step.status === "completed" ? "Completed" : "Run This Step"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* CONNECTOR */}
      {index < totalSteps - 1 && (
        <div className="flex justify-center my-2">
          <div
            className={`w-0.5 h-6 rounded-full ${
              step.status === "completed"
                ? darkMode
                  ? "bg-green-700"
                  : "bg-green-300"
                : darkMode
                ? "bg-gray-600"
                : "bg-blue-200"
            }`}
          />
        </div>
      )}
    </div>
  );
}

