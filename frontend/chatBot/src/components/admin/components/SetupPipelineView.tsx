"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Loader2, Play, Square, CheckCircle2, AlertCircle, XCircle,
  Github, Lock, Unlock, ChevronDown, X, RefreshCw, Settings, LogOut
} from "lucide-react";
import { Step } from "./types";
import StepCard from "./StepCard";
import { validateGitHubName, validateRepositoryInput } from "./validation";

interface Repository {
  name: string;
  full_name: string;
  private: boolean;
}

interface PrivateRepoState {
  owner: string;
  installation_id: number;
  account_type: "User" | "Organization";
  repositories: Repository[];
  connected_at: string;
  updated_at: string;
}

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
  const searchParams = useSearchParams();

  // Existing state
  const [orgError, setOrgError] = useState<string>("");
  const [repoError, setRepoError] = useState<string>("");
  const [touched, setTouched] = useState({ org: false, repo: false });
  const [validating, setValidating] = useState(false);

  // Private repo state
  const [repoType, setRepoType] = useState<"public" | "private">("public");
  const [privateState, setPrivateState] = useState<PrivateRepoState | null>(null);
  const [loadingState, setLoadingState] = useState(false);
  const [refreshingState, setRefreshingState] = useState(false);

  // Success banner state
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const GITHUB_APP_NAME = process.env.NEXT_PUBLIC_GITHUB_APP_NAME || "your-app-name";

  // ✅ Handle GitHub callback with proper timing
  useEffect(() => {
    const connected = searchParams.get("github_connected");
    const instId = searchParams.get("installation_id");
    const setupAction = searchParams.get("setup_action");

    if (connected === "true" || setupAction) {
      console.log("🎉 GitHub callback detected!");
      console.log("   Installation ID:", instId);
      console.log("   Setup Action:", setupAction);
      console.log("⏳ Waiting for webhook to process...");

      // Show loading state
      setShowSuccess(true);
      setSuccessMessage("Processing GitHub connection...");

      // Switch to private mode
      setRepoType("private");

      // Wait for webhook to complete (4 seconds)
      setTimeout(async () => {
        console.log("🔄 Refreshing private repo state...");
        const updated = await loadPrivateRepoState();

        if (updated) {
          console.log("✅ Private repo state loaded successfully!");
          setSuccessMessage(
            `GitHub connected! Account: ${updated.owner} - ${updated.repositories.length} repository(ies) available`
          );

          // Auto-hide success after 5 seconds
          setTimeout(() => setShowSuccess(false), 5000);
        } else {
          console.log("⚠️ No private repo state found after webhook");
          setSuccessMessage("Connected, but no repositories found. Please grant access in GitHub settings.");
        }
      }, 4000); // 4 second delay for webhook

      // Clean up URL params
      window.history.replaceState({}, "", "/manager/pipeline");
    }
  }, [searchParams]);

  // Load private repo state when switching to private mode (initial load only)
  useEffect(() => {
    if (repoType === "private" && privateState === null) {
      loadPrivateRepoState();
    }
  }, [repoType]);

  // ✅ Load private repo state from backend
  const loadPrivateRepoState = async (): Promise<PrivateRepoState | null> => {
    setLoadingState(true);
    try {
      console.log("📡 Fetching private repo state from backend...");

      const response = await fetch(`${baseURL}/api/data-collection/private-repo-state`);
      const data = await response.json();

      console.log("📦 Backend response:", data);

      if (data.connected && data.state) {
        const state = data.state as PrivateRepoState;

        setPrivateState(state);
        setOrganization(state.owner);

        console.log("✅ Private repo state loaded:", state.owner);
        console.log(`   ${state.repositories.length} repositories available`);

        return state;
      } else {
        console.log("⚠️ No private repo state found");
        setPrivateState(null);
        return null;
      }
    } catch (error) {
      console.error("❌ Failed to load private repo state:", error);
      setPrivateState(null);
      return null;
    } finally {
      setLoadingState(false);
    }
  };

  // ✅ Manual refresh button
  const handleRefresh = async () => {
    setRefreshingState(true);
    await loadPrivateRepoState();
    setRefreshingState(false);
  };

  // ✅ Connect GitHub button
  const handleConnectGitHub = () => {
    console.log("🔗 Opening GitHub app installation...");

    // Create state parameter with return URL
    const state = btoa(
      JSON.stringify({
        return_url: "/manager/pipeline",
      })
    );

    // Redirect to GitHub App installation
    const installUrl = `https://github.com/apps/${GITHUB_APP_NAME}/installations/new?state=${state}`;
    window.location.href = installUrl;
  };

  // ✅ Manage repos in GitHub
  const handleManageRepos = () => {
    if (!privateState) return;

    const installationId = privateState.installation_id;
    const manageUrl = `https://github.com/settings/installations/${installationId}`;

    console.log("⚙️ Opening GitHub settings:", manageUrl);
    window.open(manageUrl, "_blank");

    // Show user message
    alert(
      "After updating your repositories in GitHub:\n\n" +
      "1. Return to this page\n" +
      "2. Click the 'Refresh' button to load your changes"
    );
  };

  // ✅ Disconnect GitHub account
  const handleDisconnect = async () => {
    if (!privateState) return;

    if (!confirm(`Disconnect ${privateState.owner}? You'll need to reconnect to use private repos.`)) {
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/data-collection/disconnect-github`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.success) {
        setPrivateState(null);
        setOrganization("");
        setRepoName("");
        console.log("✅ Disconnected successfully");
        alert("GitHub account disconnected successfully");
      } else {
        alert(`Failed to disconnect: ${data.message}`);
      }
    } catch (error) {
      console.error("Failed to disconnect:", error);
      alert("Failed to disconnect GitHub account");
    }
  };

  // ✅ Get repositories for connected account
  const getAvailableRepos = (): Repository[] => {
    if (!privateState) return [];
    return privateState.repositories || [];
  };

  // ✅ Handle repo selection (set just repo name, not full_name)
  const handleRepoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const repoFullName = e.target.value;

    if (!repoFullName) {
      setRepoName("");
      return;
    }

    // Find the repo object
    const repo = getAvailableRepos().find((r) => r.full_name === repoFullName);

    if (repo) {
      // Set just the repo name (not full_name)
      setRepoName(repo.name);
      setTouched((prev) => ({ ...prev, repo: true }));
      setRepoError("");
    }
  };

  // Client-side format validation (only for public repos)
  useEffect(() => {
    if (repoType === "public") {
      if (touched.org || organization) {
        const validation = validateGitHubName(organization, "Organization name");
        setOrgError(validation.error || "");
      } else {
        setOrgError("");
      }
    } else {
      setOrgError("");
    }
  }, [organization, touched.org, repoType]);

  useEffect(() => {
    if (repoType === "public") {
      if (touched.repo || repoName) {
        const validation = validateGitHubName(repoName, "Repository name");
        setRepoError(validation.error || "");
      } else {
        setRepoError("");
      }
    } else {
      setRepoError("");
    }
  }, [repoName, touched.repo, repoType]);

  // Backend validation (only for public repos)
  useEffect(() => {
    if (repoType !== "public") return;

    const validateRepository = async () => {
      const orgFormatValid = !validateGitHubName(organization, "Organization name").error;
      const repoFormatValid = !validateGitHubName(repoName, "Repository name").error;

      if (!orgFormatValid || !repoFormatValid || !organization.trim() || !repoName.trim()) {
        return;
      }

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
          setOrgError("");
          setRepoError("");
        } else {
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
        }
      } catch (error: any) {
        console.error("Validation error:", error);
      } finally {
        setValidating(false);
      }
    };

    const timeoutId = setTimeout(validateRepository, 800);
    return () => clearTimeout(timeoutId);
  }, [organization, repoName, touched.org, touched.repo, repoType, baseURL]);

  const handleOrgBlur = () => {
    setTouched((prev) => ({ ...prev, org: true }));
  };

  const handleRepoBlur = () => {
    setTouched((prev) => ({ ...prev, repo: true }));
  };

  const handleSetupClick = async () => {
    if (repoType === "private") {
      // For private repos, validate selection
      if (!privateState || !repoName) {
        setRepoError("Please connect GitHub and select a repository");
        return;
      }
      handleSetup();
      return;
    }

    // For public repos, validate as before
    setTouched({ org: true, repo: true });

    const validation = validateRepositoryInput(organization, repoName);

    if (!validation.isValid) {
      setOrgError(validation.orgError || "");
      setRepoError(validation.repoError || "");
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

      handleSetup();
    } catch (error: any) {
      console.error("Validation error:", error);
      setOrgError("Failed to validate repository. Please check your connection and try again.");
      setRepoError("Failed to validate repository. Please check your connection and try again.");
    } finally {
      setValidating(false);
    }
  };

  const isFormValid =
    repoType === "private"
      ? privateState && repoName && !validating
      : !orgError && !repoError && organization.trim() && repoName.trim() && !validating;

  return (
    <div className="max-w-4xl mx-auto">
      {/* SUCCESS BANNER */}
      {showSuccess && (
        <div className="mb-6 animate-in slide-in-from-top duration-300">
          <div
            className={`rounded-lg p-4 flex items-center gap-3 ${darkMode
                ? "bg-emerald-900/20 border border-emerald-800"
                : "bg-emerald-50 border border-emerald-200"
              }`}
          >
            <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <div className="flex-1">
              <p
                className={`font-semibold ${darkMode ? "text-emerald-100" : "text-emerald-900"
                  }`}
              >
                🎉 GitHub Connected!
              </p>
              <p
                className={`text-sm ${darkMode ? "text-emerald-300" : "text-emerald-700"
                  }`}
              >
                {successMessage}
              </p>
            </div>
            <button
              onClick={() => setShowSuccess(false)}
              className={`${darkMode
                  ? "text-emerald-400 hover:text-emerald-200"
                  : "text-emerald-600 hover:text-emerald-800"
                }`}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* SETUP FORM */}
      <div
        className={`rounded-xl shadow-lg border p-6 mb-6 ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200"
          }`}
      >
        <h2
          className={`text-2xl font-semibold mb-4 ${darkMode ? "text-white" : "text-slate-900"
            }`}
        >
          Repository Setup
        </h2>

        <div className="space-y-4">
          {/* Repository Type Toggle */}
          <div
            className={`flex items-center gap-4 p-4 rounded-lg border ${darkMode ? "bg-gray-700 border-gray-600" : "bg-slate-50 border-slate-200"
              }`}
          >
            <span className={darkMode ? "text-gray-300" : "text-slate-700"}>
              Repository Type:
            </span>

            <div className="flex gap-2">
              <button
                onClick={() => setRepoType("public")}
                disabled={isRunning}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${repoType === "public"
                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md"
                    : darkMode
                      ? "bg-gray-600 text-gray-300 hover:bg-gray-500"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
              >
                <Unlock className="w-4 h-4" />
                Public
              </button>

              <button
                onClick={() => setRepoType("private")}
                disabled={isRunning}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${repoType === "private"
                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md"
                    : darkMode
                      ? "bg-gray-600 text-gray-300 hover:bg-gray-500"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
              >
                <Lock className="w-4 h-4" />
                Private
              </button>
            </div>
          </div>

          {/* PUBLIC REPO INPUTS */}
          {repoType === "public" && (
            <>
              {/* ORG */}
              <div>
                <label
                  className={`block text-sm font-medium mb-2 ${darkMode ? "text-gray-300" : "text-slate-700"
                    }`}
                >
                  Organization Name
                </label>
                <div className="relative">
                  <input
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    onBlur={handleOrgBlur}
                    disabled={isRunning}
                    placeholder="e.g., CCExtractor"
                    className={`w-full px-4 py-3 rounded-lg border-2 transition-all shadow-sm ${orgError
                        ? darkMode
                          ? "bg-gray-700 border-red-500 text-white focus:border-red-400 focus:ring-red-500/20"
                          : "bg-white border-red-400 text-slate-900 focus:border-red-500 focus:ring-red-500/20"
                        : darkMode
                          ? "bg-gray-700 border-gray-600 text-white focus:border-blue-500 focus:ring-blue-500/20"
                          : "bg-white border-slate-200 text-slate-900 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
                      } focus:ring-2 focus:outline-none ${validating && touched.org && organization.trim() ? "pr-10" : ""
                      }`}
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
                <label
                  className={`block text-sm font-medium mb-2 ${darkMode ? "text-gray-300" : "text-slate-700"
                    }`}
                >
                  Repository Name
                </label>
                <div className="relative">
                  <input
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    onBlur={handleRepoBlur}
                    disabled={isRunning}
                    placeholder="e.g., taskwarrior-flutter"
                    className={`w-full px-4 py-3 rounded-lg border-2 transition-all shadow-sm ${repoError
                        ? darkMode
                          ? "bg-gray-700 border-red-500 text-white focus:border-red-400 focus:ring-red-500/20"
                          : "bg-white border-red-400 text-slate-900 focus:border-red-500 focus:ring-red-500/20"
                        : darkMode
                          ? "bg-gray-700 border-gray-600 text-white focus:border-blue-500 focus:ring-blue-500/20"
                          : "bg-white border-slate-200 text-slate-900 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
                      } focus:ring-2 focus:outline-none ${validating && touched.repo && repoName.trim() ? "pr-10" : ""
                      }`}
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
            </>
          )}

          {/* PRIVATE REPO SELECTORS */}
          {repoType === "private" && (
            <>
              {/* Loading State */}
              {loadingState && !privateState && (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                  <span className="ml-3 text-gray-600 dark:text-gray-400">
                    Loading GitHub connection...
                  </span>
                </div>
              )}

              {/* NO CONNECTION - Show Connect Button */}
              {!loadingState && !privateState && (
                <div
                  className={`p-6 rounded-lg border-2 border-dashed text-center ${darkMode
                      ? "bg-gray-700 border-gray-600"
                      : "bg-slate-50 border-slate-300"
                    }`}
                >
                  <Github className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <h3
                    className={`text-lg font-semibold mb-2 ${darkMode ? "text-white" : "text-slate-900"
                      }`}
                  >
                    Connect Your GitHub Account
                  </h3>
                  <p
                    className={`text-sm mb-4 ${darkMode ? "text-gray-400" : "text-slate-600"
                      }`}
                  >
                    To access private repositories, connect your GitHub account
                  </p>
                  <button
                    onClick={handleConnectGitHub}
                    className="px-6 py-3 bg-[#24292e] hover:bg-[#1b1f23] text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all flex items-center gap-2 mx-auto"
                  >
                    <Github className="w-5 h-5" />
                    Connect GitHub
                  </button>
                </div>
              )}

              {/* CONNECTED - Show Account and Repos */}
              {!loadingState && privateState && (
                <>
                  {/* Connected Account Header */}
                  <div
                    className={`p-4 rounded-lg border ${darkMode
                        ? "bg-emerald-900/10 border-emerald-800"
                        : "bg-emerald-50 border-emerald-200"
                      }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                        <span
                          className={`font-semibold ${darkMode ? "text-emerald-100" : "text-emerald-900"
                            }`}
                        >
                          {privateState.account_type === "User" ? "👤" : "🏢"} {privateState.owner}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleRefresh}
                          disabled={refreshingState}
                          className={`flex items-center gap-1 text-sm ${darkMode
                              ? "text-emerald-400 hover:text-emerald-200"
                              : "text-emerald-700 hover:text-emerald-900"
                            }`}
                        >
                          <RefreshCw
                            className={`w-4 h-4 ${refreshingState ? "animate-spin" : ""
                              }`}
                          />
                          Refresh
                        </button>
                        <button
                          onClick={handleDisconnect}
                          disabled={isRunning}
                          className={`flex items-center gap-1 text-sm ${darkMode
                              ? "text-red-400 hover:text-red-200"
                              : "text-red-600 hover:text-red-800"
                            }`}
                        >
                          <LogOut className="w-4 h-4" />
                          Disconnect
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <p
                        className={`text-sm ${darkMode ? "text-emerald-300" : "text-emerald-700"
                          }`}
                      >
                        {privateState.repositories.length} repository(ies) • Installation ID: {privateState.installation_id}
                      </p>
                      <button
                        onClick={handleManageRepos}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                      >
                        <Settings className="w-3 h-3" />
                        Manage Repos
                      </button>
                    </div>
                  </div>

                  {/* Repository Selector */}
                  <div>
                    <label
                      className={`block text-sm font-medium mb-2 ${darkMode ? "text-gray-300" : "text-slate-700"
                        }`}
                    >
                      Select Repository
                    </label>
                    <div className="relative">
                      <select
                        value={
                          repoName
                            ? getAvailableRepos().find((r) => r.name === repoName)
                              ?.full_name || ""
                            : ""
                        }
                        onChange={handleRepoChange}
                        disabled={isRunning}
                        className={`w-full px-4 py-3 rounded-lg border-2 transition-all shadow-sm appearance-none cursor-pointer ${darkMode
                            ? "bg-gray-700 border-gray-600 text-white focus:border-blue-500 focus:ring-blue-500/20"
                            : "bg-white border-slate-200 text-slate-900 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
                          } focus:ring-2 focus:outline-none`}
                      >
                        <option value="">-- Select Repository --</option>
                        {getAvailableRepos().map((repo) => (
                          <option key={repo.full_name} value={repo.full_name}>
                            {repo.private ? "🔒" : "🔓"} {repo.full_name}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                    </div>
                    {getAvailableRepos().length === 0 && (
                      <p className="mt-2 text-sm text-amber-600 dark:text-amber-400">
                        ⚠️ No repositories available. Click "Manage Repos" to grant
                        access in GitHub.
                      </p>
                    )}
                    {repoError && (
                      <div className="mt-1.5 flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span>{repoError}</span>
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}

          {/* MODE TOGGLE */}
          <div
            className={`flex items-center gap-4 p-4 rounded-lg border ${darkMode ? "bg-gray-700 border-gray-600" : "bg-slate-50 border-slate-200"
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
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${executionMode === mode
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
                className={`flex-1 font-semibold py-3 rounded-lg shadow-md hover:shadow-lg transition-all ${isFormValid && !isRunning
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
              className={`p-4 rounded-lg border ${darkMode
                  ? "bg-blue-900/20 border-blue-800 text-blue-300"
                  : "bg-sky-50 border-sky-200 text-sky-700"
                }`}
            >
              <p className="font-semibold mb-1">Step-by-Step Mode</p>
              <p className="text-sm">Run each step individually from the list below.</p>
            </div>
          )}
        </div>
      </div>

      {/* PROGRESS SECTION - keeping your existing code */}
      <div
        className={`relative rounded-xl shadow-lg border p-6 ${darkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white/80 backdrop-blur-xl border-gray-200/50"
          }`}
      >
        {!darkMode && (
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />
        )}

        <div className="relative z-10">
          <h2
            className={`text-2xl font-semibold mb-6 ${darkMode ? "text-white" : "text-[#0E1B2E]"
              }`}
          >
            Setup Progress
          </h2>

          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              {steps.map((step, index) => {
                const currentStepIndex = steps.findIndex((s) => s.status === "running");
                const completedCount = steps.filter((s) => s.status === "completed").length;
                const isActive =
                  currentStepIndex === index ||
                  (currentStepIndex === -1 && index === completedCount);
                const isCompleted = step.status === "completed";
                const isError = step.status === "error";

                return (
                  <div key={step.id} className="flex-1 flex items-center">
                    <div className="flex flex-col items-center flex-1">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${isCompleted
                            ? "bg-emerald-500 border-emerald-600 text-white"
                            : isError
                              ? "bg-rose-500 border-rose-600 text-white"
                              : isActive && step.status === "running"
                                ? "bg-[#0E1B2E] border-[#0E1B2E] text-white ring-4 ring-[#0E1B2E]/20 animate-pulse"
                                : isActive
                                  ? "bg-[#0E1B2E] border-[#0E1B2E] text-white"
                                  : "bg-white border-gray-300 text-gray-400"
                          }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="w-6 h-6" />
                        ) : isError ? (
                          <XCircle className="w-6 h-6" />
                        ) : step.status === "running" ? (
                          <Loader2 className="w-6 h-6 animate-spin" />
                        ) : (
                          <span className="text-sm font-semibold">{index + 1}</span>
                        )}
                      </div>
                      <div className="mt-2 text-center max-w-[120px]">
                        <p
                          className={`text-xs font-medium ${isActive || isCompleted
                              ? darkMode
                                ? "text-white"
                                : "text-[#0E1B2E]"
                              : "text-gray-400"
                            }`}
                        >
                          {step.name}
                        </p>
                      </div>
                    </div>

                    {index < steps.length - 1 && (
                      <div className="flex-1 h-0.5 mx-2 -mt-6 relative">
                        <div
                          className={`absolute inset-0 transition-all ${isCompleted
                              ? "bg-emerald-500"
                              : completedCount > index
                                ? "bg-emerald-500"
                                : "bg-gray-200"
                            }`}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {steps.some((s) => s.status === "running") &&
              (() => {
                const currentStep = steps.find((s) => s.status === "running");
                const currentIndex = steps.findIndex((s) => s.status === "running");
                if (!currentStep) return null;

                return (
                  <div className="mt-6 p-4 rounded-xl bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-[#0E1B2E] flex items-center justify-center">
                        <span className="text-white font-bold text-sm">
                          Step {currentIndex + 1}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-[#0E1B2E]">{currentStep.name}</p>
                        <p className="text-sm text-[#0E1B2E]/60">
                          {currentStep.description}
                        </p>
                        {currentStep.message && (
                          <p className="text-xs text-[#0E1B2E]/70 mt-1">
                            {currentStep.message}
                          </p>
                        )}
                      </div>
                      <Loader2 className="w-5 h-5 animate-spin text-[#0E1B2E]" />
                    </div>
                  </div>
                );
              })()}
          </div>

          {executionMode === "step-by-step" && (
            <div className="space-y-3">
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
          )}

          {steps.every((s) => s.status === "completed") && (
            <div className="mt-6 p-4 rounded-xl border bg-emerald-50/80 border-emerald-200/50 text-emerald-700 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5" />
                Setup completed successfully!
              </div>
            </div>
          )}

          {steps.some((s) => s.status === "error") && (
            <div className="mt-6 p-4 rounded-xl border bg-rose-50/80 border-rose-200/50 text-rose-700 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Setup encountered an error. Please retry.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
