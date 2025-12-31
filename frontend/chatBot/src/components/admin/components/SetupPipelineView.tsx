"use client";

import { useState, useEffect } from "react";
import { Loader2, Play, Square, CheckCircle2, AlertCircle } from "lucide-react";
import { Step } from "./types";
import StepCard from "./StepCard";
import { validateGitHubName, validateRepositoryInput } from "./validation";

interface SetupPipelineViewProps {
  darkMode: boolean;
  organization: string;
  setOrganization: (value: string) => void;
  repoName: string;
  setRepoName: (value: string) => void;
  isRunning: boolean;
  executionMode: "full" | "step-by-step";
  setExecutionMode: (mode: "full" | "step-by-step") => void;
  canCancel: boolean;
  steps: Step[];
  handleSetup: () => void;
  handleCancel: () => void;
  handleStepByStep: (stepId: string) => void;
}

export default function SetupPipelineView({
  darkMode,
  organization,
  setOrganization,
  repoName,
  setRepoName,
  isRunning,
  executionMode,
  setExecutionMode,
  canCancel,
  steps,
  handleSetup,
  handleCancel,
  handleStepByStep,
}: SetupPipelineViewProps) {
  const [orgError, setOrgError] = useState<string>("");
  const [repoError, setRepoError] = useState<string>("");
  const [touched, setTouched] = useState({ org: false, repo: false });
  const [validating, setValidating] = useState(false);

  // Client-side format validation
  useEffect(() => {
    if (touched.org || organization) {
      const validation = validateGitHubName(organization, "Organization name");
      setOrgError(validation.error || "");
    } else {
      setOrgError("");
    }
  }, [organization, touched.org]);

  useEffect(() => {
    if (touched.repo || repoName) {
      const validation = validateGitHubName(repoName, "Repository name");
      setRepoError(validation.error || "");
    } else {
      setRepoError("");
    }
  }, [repoName, touched.repo]);

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Backend validation - validate repository existence when both fields are filled
  useEffect(() => {
    const validateRepository = async () => {
      // Only validate if both fields have values and pass format validation
      const orgFormatValid = !validateGitHubName(organization, "Organization name").error;
      const repoFormatValid = !validateGitHubName(repoName, "Repository name").error;
      
      if (!orgFormatValid || !repoFormatValid || !organization.trim() || !repoName.trim()) {
        return;
      }

      // Only validate if user has interacted with both fields
      if (!touched.org || !touched.repo) {
        return;
      }

      setValidating(true);
      
      try {
        const response = await fetch(`${baseURL}/admin/validate-repository`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            organization: organization.trim(),
            repo_name: repoName.trim(),
          }),
        });

        const data = await response.json();

        if (data.is_valid) {
          // Clear errors if validation passes
          setOrgError("");
          setRepoError("");
        } else {
          // Set appropriate error based on field
          if (data.field === "organization") {
            setOrgError(data.error || "Invalid organization name");
            setRepoError("");
          } else if (data.field === "repo_name") {
            setRepoError(data.error || "Invalid repository name");
            setOrgError("");
          } else {
            // Error applies to both fields
            setOrgError(data.error || "Repository validation failed");
            setRepoError(data.error || "Repository validation failed");
          }
        }
      } catch (error: any) {
        console.error("Validation error:", error);
        // Don't set error on network failure, just log it
      } finally {
        setValidating(false);
      }
    };

    // Debounce validation - wait 800ms after user stops typing
    const timeoutId = setTimeout(validateRepository, 800);
    return () => clearTimeout(timeoutId);
  }, [organization, repoName, touched.org, touched.repo]);

  const handleOrgBlur = () => {
    setTouched((prev) => ({ ...prev, org: true }));
  };

  const handleRepoBlur = () => {
    setTouched((prev) => ({ ...prev, repo: true }));
  };

  const handleSetupClick = async () => {
    // Mark both fields as touched
    setTouched({ org: true, repo: true });

    // First, validate format
    const validation = validateRepositoryInput(organization, repoName);
    
    if (!validation.isValid) {
      setOrgError(validation.orgError || "");
      setRepoError(validation.repoError || "");
      return;
    }

    // Then validate repository existence via backend
    setValidating(true);
    try {
      const response = await fetch(`${baseURL}/admin/validate-repository`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          organization: organization.trim(),
          repo_name: repoName.trim(),
        }),
      });

      const data = await response.json();

      if (!data.is_valid) {
        if (data.field === "organization") {
          setOrgError(data.error || "Invalid organization name");
          setRepoError("");
        } else if (data.field === "repo_name") {
          setRepoError(data.error || "Invalid repository name");
          setOrgError("");
        } else {
          setOrgError(data.error || "Repository validation failed");
          setRepoError(data.error || "Repository validation failed");
        }
        return;
      }

      // If validation passes, proceed with setup
      handleSetup();
    } catch (error: any) {
      console.error("Validation error:", error);
      setOrgError("Failed to validate repository. Please check your connection and try again.");
      setRepoError("Failed to validate repository. Please check your connection and try again.");
    } finally {
      setValidating(false);
    }
  };

  const isFormValid = !orgError && !repoError && organization.trim() && repoName.trim() && !validating;

  return (
    <div className="max-w-4xl mx-auto">
      {/* SETUP FORM */}
      <div
        className={`rounded-xl shadow-lg border p-6 mb-6 ${
          darkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-slate-200"
        }`}
      >
        <h2
          className={`text-2xl font-semibold mb-4 ${
            darkMode ? "text-white" : "text-slate-900"
          }`}
        >
          Repository Setup
        </h2>

        <div className="space-y-4">
          {/* ORG */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>
              Organization Name
            </label>
            <div className="relative">
              <input
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                onBlur={handleOrgBlur}
                disabled={isRunning}
                placeholder="e.g., CCExtractor"
                className={`w-full px-4 py-3 rounded-lg border-2 transition-all shadow-sm ${
                  orgError
                    ? darkMode
                      ? "bg-gray-700 border-red-500 text-white focus:border-red-400 focus:ring-red-500/20"
                      : "bg-white border-red-400 text-slate-900 focus:border-red-500 focus:ring-red-500/20"
                    : darkMode
                    ? "bg-gray-700 border-gray-600 text-white focus:border-blue-500 focus:ring-blue-500/20"
                    : "bg-white border-slate-200 text-slate-900 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
                } focus:ring-2 focus:outline-none ${validating && touched.org && organization.trim() ? "pr-10" : ""}`}
              />
              {validating && touched.org && organization.trim() && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                </div>
              )}
            </div>
            {orgError && (
              <div className="mt-1.5 flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{orgError}</span>
              </div>
            )}
          </div>

          {/* REPO */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>
              Repository Name
            </label>
            <div className="relative">
              <input
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                onBlur={handleRepoBlur}
                disabled={isRunning}
                placeholder="e.g., taskwarrior-flutter"
                className={`w-full px-4 py-3 rounded-lg border-2 transition-all shadow-sm ${
                  repoError
                    ? darkMode
                      ? "bg-gray-700 border-red-500 text-white focus:border-red-400 focus:ring-red-500/20"
                      : "bg-white border-red-400 text-slate-900 focus:border-red-500 focus:ring-red-500/20"
                    : darkMode
                    ? "bg-gray-700 border-gray-600 text-white focus:border-blue-500 focus:ring-blue-500/20"
                    : "bg-white border-slate-200 text-slate-900 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
                } focus:ring-2 focus:outline-none ${validating && touched.repo && repoName.trim() ? "pr-10" : ""}`}
              />
              {validating && touched.repo && repoName.trim() && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                </div>
              )}
            </div>
            {repoError && (
              <div className="mt-1.5 flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{repoError}</span>
              </div>
            )}
          </div>

          {/* MODE TOGGLE */}
          <div
            className={`flex items-center gap-4 p-4 rounded-lg border ${
              darkMode
                ? "bg-gray-700 border-gray-600"
                : "bg-slate-50 border-slate-200"
            }`}
          >
            <span className={darkMode ? "text-gray-300" : "text-slate-700"}>
              Execution Mode:
            </span>

            <div className="flex gap-2">
              {["full", "step-by-step"].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setExecutionMode(mode as any)}
                  disabled={isRunning}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    executionMode === mode
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md"
                      : darkMode
                      ? "bg-gray-600 text-gray-300 hover:bg-gray-500"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {mode === "full" ? "Full Pipeline" : "Step by Step"}
                </button>
              ))}
            </div>
          </div>

          {/* ACTIONS */}
          {executionMode === "full" ? (
            <div className="flex gap-3">
              <button
                onClick={handleSetupClick}
                disabled={isRunning || !isFormValid}
                className={`flex-1 font-semibold py-3 rounded-lg shadow-md hover:shadow-lg transition-all ${
                  isFormValid && !isRunning
                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
                    : "bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                }`}
              >
                {isRunning ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running Pipeline...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Play className="w-5 h-5" />
                    Start Full Pipeline
                  </span>
                )}
              </button>

              {canCancel && (
                <button
                  onClick={handleCancel}
                  className="bg-gradient-to-r from-rose-500 to-red-600 hover:from-red-600 hover:to-rose-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:shadow-lg"
                >
                  <Square className="w-5 h-5" />
                </button>
              )}
            </div>
          ) : (
            <div
              className={`p-4 rounded-lg border ${
                darkMode
                  ? "bg-blue-900/20 border-blue-800 text-blue-300"
                  : "bg-sky-50 border-sky-200 text-sky-700"
              }`}
            >
              <p className="font-semibold mb-1">Step-by-Step Mode</p>
              <p className="text-sm">
                Run each step individually from the list below.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* PROGRESS */}
      <div
        className={`rounded-xl shadow-lg border p-6 ${
          darkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-slate-200"
        }`}
      >
        <h2
          className={`text-2xl font-semibold mb-6 ${
            darkMode ? "text-white" : "text-slate-900"
          }`}
        >
          Setup Progress
        </h2>

        <div className="space-y-4">
          {steps.map((step, index) => (
            <StepCard
              key={step.id}
              step={step}
              index={index}
              totalSteps={steps.length}
              darkMode={darkMode}
              executionMode={executionMode}
              isRunning={isRunning}
              organization={organization}
              repoName={repoName}
              onRunStep={handleStepByStep}
            />
          ))}
        </div>

        {/* SUMMARY */}
        {steps.every((s) => s.status === "completed") && (
          <div className="mt-6 p-4 rounded-lg border bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              Setup completed successfully!
            </div>
          </div>
        )}

        {steps.some((s) => s.status === "error") && (
          <div className="mt-6 p-4 rounded-lg border bg-rose-50 border-rose-200 text-rose-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Setup encountered an error. Please retry.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

