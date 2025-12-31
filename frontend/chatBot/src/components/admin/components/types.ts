export type StepStatus = "pending" | "running" | "completed" | "error";

export interface Step {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  message?: string;
}

export interface SetupStats {
  totalSetups: number;
  successfulSetups: number;
  failedSetups: number;
  lastSetup: string | null;
}

export interface HistoryEntry {
  id: number;
  organization?: string;
  repo?: string;
  status: "success" | "failed";
  timestamp: string;
  duration?: number;
  error?: string;
  execution_mode?: "full" | "step-by-step";
  step?: string; // For step-by-step: "data-collection", "data-processing", "embedding", "vectordb"
  step_name?: string; // Human-readable step name
  action_type?: "setup" | "onboarding" | "offboarding"; // Type of action
  // Onboarding specific fields
  selected_generators?: string[]; // List of selected generator IDs
  categories?: string[]; // List of categories that were run (reading, bugfix, practice, qna)
  generator_count?: number; // Total number of generators run
  // Offboarding specific fields
  offboarding_type?: string; // Type of offboarding if applicable
  selected_steps?: string[]; // List of selected step IDs for offboarding
  step_count?: number; // Total number of steps run
}

