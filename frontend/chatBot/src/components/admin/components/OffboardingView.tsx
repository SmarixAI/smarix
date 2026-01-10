"use client";

import { useState, useEffect } from "react";
import { Loader2, FileText, CheckCircle2, AlertCircle, Users, FileCode, AlertTriangle, ClipboardList, FileCheck, BookOpen } from "lucide-react";
import { StepStatus } from "./types";
import { getStepIcon } from "./StepCard";
import { Space_Grotesk, Fira_Code } from 'next/font/google';
import Image from 'next/image';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const firaCode = Fira_Code({ subsets: ['latin'] });

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
      <div className="relative rounded-xl shadow-lg p-6 bg-white/80 backdrop-blur-xl border border-gray-200/50">
        {/* Grid pattern background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#0E1B2E] rounded-xl flex items-center justify-center overflow-hidden">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={24}
                  height={24}
                  className="w-6 h-6 object-contain"
                />
              </div>
              <div>
                <h2 className={`${spaceGrotesk.className} text-2xl font-bold mb-1 text-[#0E1B2E]`}>
                  Offboarding Data Generation
                </h2>
                <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}>
                  Generate comprehensive offboarding documentation and handover materials
                </p>
              </div>
            </div>
          </div>

          {/* EMPLOYEE NAME INPUT */}
          <div className="mb-6">
            <div className="mb-4">
              <label
                htmlFor="employee-name"
                className={`${spaceGrotesk.className} block text-sm font-medium mb-2 text-[#0E1B2E]`}
              >
                Employee Name <span className="text-rose-600">*</span>
              </label>
              <p className={`${firaCode.className} text-xs mb-3 text-[#0E1B2E]/60`}>
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
                className={`${firaCode.className} w-full px-4 py-2.5 rounded-xl border transition-all ${
                  employeeName.trim()
                    ? "bg-white/80 backdrop-blur-sm border-gray-200/50 text-[#0E1B2E] placeholder-[#0E1B2E]/40 focus:border-[#0E1B2E] focus:ring-2 focus:ring-[#0E1B2E]/10"
                    : "bg-white/80 backdrop-blur-sm border-rose-300 text-[#0E1B2E] placeholder-[#0E1B2E]/40 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/10"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              />
              {!employeeName.trim() && (
                <p className={`mt-2 text-xs ${firaCode.className} text-rose-600`}>
                  ⚠️ Employee name is required to generate offboarding data
                </p>
              )}
              {employeeName.trim() && (
                <p className={`mt-2 text-xs ${firaCode.className} text-emerald-600`}>
                  ✓ Data will be generated for "{employeeName.trim()}"
                </p>
              )}
            </div>
          </div>

          {/* STATUS CARD */}
          <div
            className={`p-6 rounded-xl border transition-all mb-6 backdrop-blur-sm ${
              offboardingStatus === "completed"
                ? "border-emerald-200/50 bg-emerald-50/80"
                : offboardingStatus === "running"
                ? "border-sky-200/50 bg-sky-50/80 ring-2 ring-sky-200/30"
                : offboardingStatus === "error"
                ? "border-rose-200/50 bg-rose-50/80"
                : "border-gray-200/50 bg-gray-50/80"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStepIcon(offboardingStatus)}
                <div>
                  <h3 className={`${spaceGrotesk.className} text-lg font-semibold text-[#0E1B2E]`}>
                    Offboarding Generation Status
                  </h3>
                  <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}>
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
                className={`${spaceGrotesk.className} px-6 py-2.5 rounded-xl font-medium transition-all ${
                  offboardingRunning || selectedSteps.length === 0 || !employeeName.trim()
                    ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                    : "bg-[#0E1B2E] hover:bg-[#0E1B2E]/90 text-white shadow-lg shadow-[#0E1B2E]/20 hover:shadow-xl hover:shadow-[#0E1B2E]/30"
                } disabled:shadow-none`}
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
                className={`mt-4 p-3 rounded-lg text-sm ${firaCode.className} ${
                  offboardingStatus === "completed"
                    ? "bg-emerald-100/80 text-emerald-700 border border-emerald-200/50"
                    : offboardingStatus === "error"
                    ? "bg-rose-100/80 text-rose-700 border border-rose-200/50"
                    : "bg-sky-100/80 text-sky-700 border border-sky-200/50"
                }`}
              >
                {offboardingMessage}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* OUTPUT FILES SECTION */}
      {offboardingStatus === "completed" && (
        <div className="relative rounded-xl shadow-lg p-6 bg-white/80 backdrop-blur-xl border border-gray-200/50">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />
          <div className="relative z-10">
            <h3 className={`${spaceGrotesk.className} text-xl font-semibold mb-4 text-[#0E1B2E]`}>
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
                      className="p-3 rounded-xl border border-gray-200/50 bg-white/50 backdrop-blur-sm"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className="w-4 h-4 text-[#0E1B2E]/70" />
                        <span className={`${firaCode.className} text-xs font-semibold px-1.5 py-0.5 rounded bg-[#0E1B2E]/10 text-[#0E1B2E]`}>
                          {index + 1}
                        </span>
                        <span className={`${spaceGrotesk.className} text-sm font-medium text-[#0E1B2E]`}>
                          {step.name}
                        </span>
                      </div>
                      <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                        {step.outputFile}
                      </p>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

