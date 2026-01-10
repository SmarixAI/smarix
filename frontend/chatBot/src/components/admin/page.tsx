"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/admin/components/Sidebar";
import SetupPipelineView from "@/components/admin/components/SetupPipelineView";
import HistoryView from "@/components/admin/components/HistoryView";
import OnboardingView from "@/components/admin/components/OnboardingView";
import OffboardingView from "@/components/admin/components/OffboardingView";
import UserManagementView from "@/components/admin/components/UserManagementView";
import ChangePasswordModal from "@/components/auth/ChangePasswordModal";
import { Step, StepStatus, HistoryEntry } from "@/components/admin/components/types";
import { validateGitHubName } from "@/components/admin/components/validation";

export default function AdminPage() {
  const [activeView, setActiveView] = useState("setup");
  const [organization, setOrganization] = useState("");
  const [repoName, setRepoName] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [executionMode, setExecutionMode] = useState<"full" | "step-by-step">("full");
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [canCancel, setCanCancel] = useState(false);
  const [setupHistory, setSetupHistory] = useState<HistoryEntry[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<StepStatus>("pending");
  const [onboardingMessage, setOnboardingMessage] = useState<string>("");
  const [onboardingRunning, setOnboardingRunning] = useState(false);
  const [offboardingStatus, setOffboardingStatus] = useState<StepStatus>("pending");
  const [offboardingMessage, setOffboardingMessage] = useState<string>("");
  const [offboardingRunning, setOffboardingRunning] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load history from backend API
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await fetch(`${baseURL}/admin/history`);
        if (response.ok) {
          const data = await response.json();
          const history = data.history || [];
          setSetupHistory(history);
        }
      } catch (error) {
        console.error("Error loading history:", error);
      }
    };
    loadHistory();
  }, []);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [wsConnection]);

  const [steps, setSteps] = useState<Step[]>([
    {
      id: "data-collection",
      name: "Data Collection",
      description: "Collecting data from GitHub repository",
      status: "pending",
    },
    {
      id: "data-processing",
      name: "Data Processing",
      description: "Processing and chunking collected data",
      status: "pending",
    },
    {
      id: "embedding",
      name: "Embedding Generation",
      description: "Generating embeddings for processed chunks",
      status: "pending",
    },
    {
      id: "vectordb",
      name: "VectorDB Storage",
      description: "Building and storing vector database indices",
      status: "pending",
    },
  ]);

  // Debug: Log step changes
  useEffect(() => {
    console.log("Steps updated:", steps.map(s => ({ id: s.id, status: s.status, message: s.message })));
  }, [steps]);

  const updateStepStatus = (stepId: string, status: StepStatus, message?: string) => {
    setSteps((prev) =>
      prev.map((step) =>
        step.id === stepId ? { ...step, status, message } : step
      )
    );
  };

  const handleCancel = async () => {
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
    }
    
    try {
      await fetch(`${baseURL}/admin/setup/cancel`, {
        method: "POST",
      });
    } catch (error) {
      console.error("Error cancelling pipeline:", error);
    }
    
    setIsRunning(false);
    setCanCancel(false);
    
    // Mark current running step as cancelled
    const currentStep = steps.find((s) => s.status === "running");
    if (currentStep) {
      updateStepStatus(currentStep.id, "error", "Pipeline was cancelled");
    }
  };

  const handleFullPipeline = async () => {
    // First validate format
    const orgValidation = validateGitHubName(organization.trim(), "Organization name");
    const repoValidation = validateGitHubName(repoName.trim(), "Repository name");
    
    if (!orgValidation.isValid || !repoValidation.isValid) {
      alert(
        `Please fix the validation errors:\n${orgValidation.error || ""}\n${repoValidation.error || ""}`
      );
      return;
    }

    if (!organization.trim() || !repoName.trim()) {
      alert("Please enter both organization name and repository name");
      return;
    }

    // Then validate repository existence via backend
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
        alert(`Repository validation failed: ${data.error || "Repository not found or inaccessible"}`);
        return;
      }
    } catch (error: any) {
      console.error("Validation error:", error);
      alert("Failed to validate repository. Please check your connection and try again.");
      return;
    }

    setIsRunning(true);
    setCanCancel(true);
    const setupStartTime = Date.now();
    
    // Reset all steps to pending
    setSteps((prev) =>
      prev.map((step) => ({ ...step, status: "pending" as StepStatus, message: undefined }))
    );

    // Connect to WebSocket
    const ws = new WebSocket(`${baseURL}/ws/admin/pipeline`);
    setWsConnection(ws);

    ws.onopen = () => {
      // Send start message
      ws.send(JSON.stringify({
        action: "start",
        request: {
          organization: organization.trim(),
          repo_name: repoName.trim(),
        },
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data);
      
      switch (data.type) {
        case "step_start":
          console.log(`Starting step: ${data.step}`);
          updateStepStatus(data.step, "running", data.message);
          break;
          
        case "step_complete":
          console.log(`Completed step: ${data.step}`);
          updateStepStatus(data.step, "completed", data.message);
          break;
          
        case "step_error":
          updateStepStatus(data.step, "error", data.message);
          setIsRunning(false);
          setCanCancel(false);
          ws.close();
          setWsConnection(null);
          
          // Save failed setup to history
          const failedEntry = {
            id: Date.now(),
            organization: organization.trim(),
            repo: repoName.trim(),
            status: "failed" as const,
            timestamp: new Date().toISOString(),
            error: data.message,
            execution_mode: "full" as const,
            action_type: "setup" as const,
          };
          // Save to backend (async IIFE)
          (async () => {
            try {
              const response = await fetch(`${baseURL}/admin/history`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(failedEntry),
              });
              if (response.ok) {
                const responseData = await response.json();
                const updatedHistory = responseData.history || [];
                setSetupHistory(updatedHistory);
                setStats({
                  totalSetups: updatedHistory.length,
                  successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
                  failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
                  lastSetup: failedEntry.timestamp,
                });
              }
            } catch (error) {
              console.error("Error saving history:", error);
            }
          })();
          break;
          
        case "cancelled":
          updateStepStatus(data.step, "error", "Pipeline was cancelled");
          setIsRunning(false);
          setCanCancel(false);
          ws.close();
          setWsConnection(null);
          break;
          
        case "complete":
          // All steps completed
          const historyEntry = {
            id: Date.now(),
            organization: organization.trim(),
            repo: repoName.trim(),
            status: "success" as const,
            timestamp: new Date().toISOString(),
            duration: Date.now() - setupStartTime,
            execution_mode: "full" as const,
            action_type: "setup" as const,
          };
          // Save to backend (async IIFE)
          (async () => {
            try {
              const response = await fetch(`${baseURL}/admin/history`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(historyEntry),
              });
              if (response.ok) {
                const responseData = await response.json();
                const updatedHistory = responseData.history || [];
                setSetupHistory(updatedHistory);
                setStats({
                  totalSetups: updatedHistory.length,
                  successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
                  failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
                  lastSetup: historyEntry.timestamp,
                });
              }
            } catch (error) {
              console.error("Error saving history:", error);
            }
          })();
          
          setIsRunning(false);
          setCanCancel(false);
          ws.close();
          setWsConnection(null);
          break;
          
        case "error":
          const currentStep = steps.find((s) => s.status === "running");
          if (currentStep) {
            updateStepStatus(currentStep.id, "error", data.message);
          }
          setIsRunning(false);
          setCanCancel(false);
          ws.close();
          setWsConnection(null);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsRunning(false);
      setCanCancel(false);
      setWsConnection(null);
    };

    ws.onclose = () => {
      setWsConnection(null);
      if (isRunning) {
        setIsRunning(false);
        setCanCancel(false);
      }
    };
  };

  const handleStepByStep = async (stepId: string) => {
    // First validate format
    const orgValidation = validateGitHubName(organization.trim(), "Organization name");
    const repoValidation = validateGitHubName(repoName.trim(), "Repository name");
    
    if (!orgValidation.isValid || !repoValidation.isValid) {
      alert(
        `Please fix the validation errors:\n${orgValidation.error || ""}\n${repoValidation.error || ""}`
      );
      return;
    }

    if (!organization.trim() || !repoName.trim()) {
      alert("Please enter both organization name and repository name");
      return;
    }

    // Then validate repository existence via backend
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
        alert(`Repository validation failed: ${data.error || "Repository not found or inaccessible"}`);
        return;
      }
    } catch (error: any) {
      console.error("Validation error:", error);
      alert("Failed to validate repository. Please check your connection and try again.");
      return;
    }

    const step = steps.find((s) => s.id === stepId);
    if (!step || step.status === "running") {
      return;
    }

    updateStepStatus(stepId, "running", `Starting ${step.name}...`);
    const stepStartTime = Date.now();

    try {
      const endpointMap: Record<string, string> = {
        "data-collection": "/admin/setup/data-collection",
        "data-processing": "/admin/setup/data-processing",
        "embedding": "/admin/setup/embedding",
        "vectordb": "/admin/setup/vectordb",
      };

      const endpoint = endpointMap[stepId];
      if (!endpoint) {
        throw new Error(`Unknown step: ${stepId}`);
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          organization: organization.trim(),
          repo_name: repoName.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `${step.name} failed`);
      }

      const data = await response.json();
      const stepDuration = Date.now() - stepStartTime;
      
      updateStepStatus(stepId, "completed", data.message || `${step.name} completed`);
      
      // Save step history
      const stepHistoryEntry = {
        id: Date.now(),
        organization: organization.trim(),
        repo: repoName.trim(),
        status: "success" as const,
        timestamp: new Date().toISOString(),
        duration: stepDuration,
        execution_mode: "step-by-step" as const,
        step: stepId,
        step_name: step.name,
        action_type: "setup" as const,
      };

      const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      try {
        const historyResponse = await fetch(`${baseURL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(stepHistoryEntry),
        });
        
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: stepHistoryEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving step history:", historyError);
      }
    } catch (error: any) {
      const stepDuration = Date.now() - stepStartTime;
      updateStepStatus(stepId, "error", error.message || `An error occurred during ${step.name}`);
      console.error(`Error in ${stepId}:`, error);
      
      // Save failed step history
      const stepHistoryEntry = {
        id: Date.now(),
        organization: organization.trim(),
        repo: repoName.trim(),
        status: "failed" as const,
        timestamp: new Date().toISOString(),
        duration: stepDuration,
        error: error.message || `An error occurred during ${step.name}`,
        execution_mode: "step-by-step" as const,
        step: stepId,
        step_name: step.name,
        action_type: "setup" as const,
      };
      
      try {
        const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(stepHistoryEntry),
        });
        
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: stepHistoryEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving step history:", historyError);
      }
    }
  };

  const handleSetup = async () => {
    if (executionMode === "full") {
      await handleFullPipeline();
    }
    // For step-by-step mode, individual steps are handled via handleStepByStep function
  };

  const handleOnboarding = async (selectedGenerators: string[]) => {
    setOnboardingRunning(true);
    setOnboardingStatus("running");
    setOnboardingMessage(`Starting onboarding data generation for ${selectedGenerators.length} generator(s)...`);

    const startTime = Date.now();
    
    // Determine which categories were selected based on generator IDs
    const categoryMap: { [key: string]: string } = {
      // Reading generators
      'repo_structure': 'reading',
      'tech_stacks': 'reading',
      'reading_overview': 'reading',
      'app_features': 'reading',
      'dev_setup': 'reading',
      'code_conventions': 'reading',
      // BugFix generators
      'coding_questions': 'bugfix',
      'pr_tutorials': 'bugfix',
      'challenge_solution': 'bugfix',
      'challenge_submitted_code': 'bugfix',
      // Practice generators
      'practice_questions': 'practice',
      // QnA generators
      'repo_structure_questions': 'qna',
      'tech_stack_questions': 'qna',
      'overview_questions': 'qna',
      'app_features_questions': 'qna',
      'dev_setup_questions': 'qna',
      'code_conventions_questions': 'qna',
    };
    
    const selectedCategories = Array.from(new Set(
      selectedGenerators.map(genId => categoryMap[genId]).filter(Boolean)
    ));

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/onboarding/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          generators: selectedGenerators
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Onboarding generation failed");
      }

      const data = await response.json();
      const duration = Date.now() - startTime;
      
      setOnboardingStatus("completed");
      setOnboardingMessage(data.message || "Onboarding data generation completed successfully");

      // Save successful history entry
      const historyEntry = {
        id: Date.now(),
        status: "success" as const,
        timestamp: new Date().toISOString(),
        duration: duration,
        action_type: "onboarding" as const,
        selected_generators: selectedGenerators,
        categories: selectedCategories,
        generator_count: selectedGenerators.length,
      };

      try {
        const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(historyEntry),
        });

        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: historyEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving onboarding history:", historyError);
      }
    } catch (error: any) {
      const duration = Date.now() - startTime;
      setOnboardingStatus("error");
      setOnboardingMessage(error.message || "An error occurred during onboarding generation");
      console.error("Error in onboarding:", error);

      // Save failed history entry
      const historyEntry = {
        id: Date.now(),
        status: "failed" as const,
        timestamp: new Date().toISOString(),
        duration: duration,
        error: error.message || "An error occurred during onboarding generation",
        action_type: "onboarding" as const,
        selected_generators: selectedGenerators,
        categories: selectedCategories,
        generator_count: selectedGenerators.length,
      };

      try {
        const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(historyEntry),
        });

        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: historyEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving onboarding history:", historyError);
      }
    } finally {
      setOnboardingRunning(false);
    }
  };

  const handleOffboarding = async (selectedSteps: string[], employeeName: string) => {
    if (!employeeName || !employeeName.trim()) {
      setOffboardingStatus("error");
      setOffboardingMessage("Employee name is required to generate offboarding data");
      return;
    }

    setOffboardingRunning(true);
    setOffboardingStatus("running");
    setOffboardingMessage(`Starting offboarding data generation for ${selectedSteps.length} step(s) for employee "${employeeName.trim()}"...`);

    const startTime = Date.now();

    try {
      const requestBody = {
        steps: selectedSteps,
        employee_name: employeeName.trim()
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/offboarding/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Offboarding generation failed");
      }

      const data = await response.json();
      const duration = Date.now() - startTime;
      
      setOffboardingStatus("completed");
      setOffboardingMessage(data.message || "Offboarding data generation completed successfully");

      // Save successful history entry
      const historyEntry = {
        id: Date.now(),
        status: "success" as const,
        timestamp: new Date().toISOString(),
        duration: duration,
        action_type: "offboarding" as const,
        selected_steps: selectedSteps,
        step_count: selectedSteps.length,
        employee_name: employeeName.trim(),
      };

      try {
        const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(historyEntry),
        });

        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: historyEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving offboarding history:", historyError);
      }
    } catch (error: any) {
      const duration = Date.now() - startTime;
      setOffboardingStatus("error");
      setOffboardingMessage(error.message || "An error occurred during offboarding generation");
      console.error("Error in offboarding:", error);

      // Save failed history entry
      const historyEntry = {
        id: Date.now(),
        status: "failed" as const,
        timestamp: new Date().toISOString(),
        duration: duration,
        error: error.message || "An error occurred during offboarding generation",
        action_type: "offboarding" as const,
        selected_steps: selectedSteps,
        step_count: selectedSteps.length,
        employee_name: employeeName.trim(),
      };

      try {
        const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/history`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(historyEntry),
        });

        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          const updatedHistory = historyData.history || [];
          setSetupHistory(updatedHistory);
          setStats({
            totalSetups: updatedHistory.length,
            successfulSetups: updatedHistory.filter((h) => h.status === "success").length,
            failedSetups: updatedHistory.filter((h) => h.status === "failed").length,
            lastSetup: historyEntry.timestamp,
          });
        }
      } catch (historyError) {
        console.error("Error saving offboarding history:", historyError);
      }
    } finally {
      setOffboardingRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative overflow-hidden">
      {/* Grid Pattern Background - matching landing page */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

      <div className="h-screen relative flex">
        {/* Fixed Sidebar */}
        <Sidebar
          activeView={activeView}
          setActiveView={setActiveView}
          onOpenChangePassword={() => setShowChangePassword(true)}
        />

        {/* Scrollable Main Content */}
        <main className="flex-1 relative z-10 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {activeView === "setup" && (
              <SetupPipelineView
                darkMode={false}
                organization={organization}
                setOrganization={setOrganization}
                repoName={repoName}
                setRepoName={setRepoName}
                isRunning={isRunning}
                executionMode={executionMode}
                setExecutionMode={setExecutionMode}
                canCancel={canCancel}
                steps={steps}
                handleSetup={handleSetup}
                handleCancel={handleCancel}
                handleStepByStep={handleStepByStep}
              />
            )}

            {activeView === "history" && (
              <HistoryView
                darkMode={false}
                setupHistory={setupHistory}
              />
            )}

            {activeView === "onboarding" && (
              <OnboardingView
                darkMode={false}
                onboardingStatus={onboardingStatus}
                onboardingMessage={onboardingMessage}
                onboardingRunning={onboardingRunning}
                onRunOnboarding={handleOnboarding}
              />
            )}

            {activeView === "offboarding" && (
              <OffboardingView
                darkMode={false}
                offboardingStatus={offboardingStatus}
                offboardingMessage={offboardingMessage}
                offboardingRunning={offboardingRunning}
                onRunOffboarding={handleOffboarding}
              />
            )}

            {activeView === "users" && (
              <UserManagementView darkMode={false} />
            )}
          </div>
        </main>
      </div>

      {/* Change Password Modal - Rendered at layout level for proper z-index */}
      <ChangePasswordModal
        isOpen={showChangePassword}
        onClose={() => setShowChangePassword(false)}
        darkMode={false}
      />
    </div>
  );
}
