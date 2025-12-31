"use client";

import { useState, useEffect } from "react";
import { Loader2, FileText, CheckCircle2, AlertCircle, Info, FolderOpen, Clock, BookOpen, Code, Settings, Layers, Bug, GraduationCap, MessageSquare } from "lucide-react";
import { StepStatus } from "./types";
import { getStepIcon } from "./StepCard";

interface OnboardingViewProps {
  darkMode: boolean;
  onboardingStatus: StepStatus;
  onboardingMessage: string;
  onboardingRunning: boolean;
  onRunOnboarding: (selectedGenerators: string[]) => void;
}

interface OnboardingGenerator {
  id: string;
  name: string;
  description: string;
  icon: any;
  outputFile: string;
  category: string;
}

interface OnboardingCategory {
  id: string;
  name: string;
  icon: any;
  generators: OnboardingGenerator[];
  outputDir: string;
}

const readingGenerators: OnboardingGenerator[] = [
  {
    id: "repo_structure",
    name: "Repository Structure",
    description: "Analyzes and documents the overall repository structure, directory organization, and file hierarchy",
    icon: FolderOpen,
    outputFile: "onboarding_repo_structure.json",
    category: "reading"
  },
  {
    id: "tech_stacks",
    name: "Tech Stack",
    description: "Identifies and documents all technologies, frameworks, libraries, and tools used in the project",
    icon: Layers,
    outputFile: "onboarding_tech_stack.json",
    category: "reading"
  },
  {
    id: "reading_overview",
    name: "Project Overview",
    description: "Generates a comprehensive reading guide and high-level overview of the project",
    icon: BookOpen,
    outputFile: "onboarding_project_overview.json",
    category: "reading"
  },
  {
    id: "app_features",
    name: "App Features",
    description: "Documents application features, user flows, and functional capabilities",
    icon: Code,
    outputFile: "onboarding_app_features.json",
    category: "reading"
  },
  {
    id: "dev_setup",
    name: "Development Setup",
    description: "Creates setup instructions, environment configuration, and development workflow guides",
    icon: Settings,
    outputFile: "onboarding_dev_setup.json",
    category: "reading"
  },
  {
    id: "code_conventions",
    name: "Code Conventions",
    description: "Documents coding standards, style guides, naming conventions, and best practices",
    icon: FileText,
    outputFile: "onboarding_code_conventions.json",
    category: "reading"
  }
];

const bugfixGenerators: OnboardingGenerator[] = [
  {
    id: "coding_questions",
    name: "Coding Questions",
    description: "Generates coding questions based on UI, features, and test cases",
    icon: Code,
    outputFile: "onboarding_coding_questions.json",
    category: "bugfix"
  },
  {
    id: "pr_tutorials",
    name: "PR Tutorials",
    description: "Creates pull request tutorials and code review guides",
    icon: FileText,
    outputFile: "onboarding_pr_tutorials.json",
    category: "bugfix"
  },
  {
    id: "challenge_solution",
    name: "Challenge Solutions",
    description: "Generates challenge solutions and coding problem answers",
    icon: CheckCircle2,
    outputFile: "onboarding_challenge_solution.json",
    category: "bugfix"
  },
  {
    id: "challenge_submitted_code",
    name: "Challenge Submitted Code",
    description: "Documents submitted code examples for challenges",
    icon: FileText,
    outputFile: "onboarding_challenge_submitted_code.json",
    category: "bugfix"
  }
];

const practiceGenerators: OnboardingGenerator[] = [
  {
    id: "practice_questions",
    name: "Practice Questions",
    description: "Generates practice coding questions with step-by-step tutorials (Easy, Intermediate, Hard)",
    icon: GraduationCap,
    outputFile: "onboarding_practice_questions.json",
    category: "practice"
  }
];

const qnaGenerators: OnboardingGenerator[] = [
  {
    id: "repo_structure_questions",
    name: "Repo Structure Questions",
    description: "Generates Q&A questions about repository structure and organization",
    icon: FolderOpen,
    outputFile: "onboarding_repo_structure_questions.json",
    category: "qna"
  },
  {
    id: "tech_stack_questions",
    name: "Tech Stack Questions",
    description: "Creates Q&A questions about technologies and frameworks used",
    icon: Layers,
    outputFile: "onboarding_tech_stack_questions.json",
    category: "qna"
  },
  {
    id: "overview_questions",
    name: "Overview Questions",
    description: "Generates Q&A questions about project overview and high-level concepts",
    icon: BookOpen,
    outputFile: "onboarding_overview_questions.json",
    category: "qna"
  },
  {
    id: "app_features_questions",
    name: "App Features Questions",
    description: "Creates Q&A questions about application features and functionality",
    icon: Code,
    outputFile: "onboarding_app_features_questions.json",
    category: "qna"
  },
  {
    id: "dev_setup_questions",
    name: "Dev Setup Questions",
    description: "Generates Q&A questions about development setup and configuration",
    icon: Settings,
    outputFile: "onboarding_dev_setup_questions.json",
    category: "qna"
  },
  {
    id: "code_conventions_questions",
    name: "Code Conventions Questions",
    description: "Creates Q&A questions about coding standards and conventions",
    icon: FileText,
    outputFile: "onboarding_code_conventions_questions.json",
    category: "qna"
  }
];

const categories: OnboardingCategory[] = [
  {
    id: "reading",
    name: "Reading",
    icon: BookOpen,
    generators: readingGenerators,
    outputDir: "onboarding_reading_data"
  },
  {
    id: "bugfix",
    name: "BugFix",
    icon: Bug,
    generators: bugfixGenerators,
    outputDir: "onboarding_bugfix_data"
  },
  {
    id: "practice",
    name: "Practice",
    icon: GraduationCap,
    generators: practiceGenerators,
    outputDir: "onboarding_practice_data"
  },
  {
    id: "qna",
    name: "QnA",
    icon: MessageSquare,
    generators: qnaGenerators,
    outputDir: "onboarding_QnA_data"
  }
];

// Flatten all generators for easy access
const allGenerators = categories.flatMap(cat => cat.generators);

export default function OnboardingView({
  darkMode,
  onboardingStatus,
  onboardingMessage,
  onboardingRunning,
  onRunOnboarding,
}: OnboardingViewProps) {
  const [selectedGenerators, setSelectedGenerators] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("reading");

  // Initialize with all generators selected
  useEffect(() => {
    if (selectedGenerators.length === 0) {
      setSelectedGenerators(allGenerators.map(g => g.id));
    }
  }, []);

  const toggleGenerator = (generatorId: string) => {
    setSelectedGenerators(prev =>
      prev.includes(generatorId)
        ? prev.filter(id => id !== generatorId)
        : [...prev, generatorId]
    );
  };

  const selectAllGenerators = (categoryId?: string) => {
    if (categoryId) {
      const category = categories.find(c => c.id === categoryId);
      if (category) {
        setSelectedGenerators(prev => {
          const categoryIds = category.generators.map(g => g.id);
          const newSelected = [...prev.filter(id => !categoryIds.includes(id)), ...categoryIds];
          return newSelected;
        });
      }
    } else {
      setSelectedGenerators(allGenerators.map(g => g.id));
    }
  };

  const deselectAllGenerators = (categoryId?: string) => {
    if (categoryId) {
      const category = categories.find(c => c.id === categoryId);
      if (category) {
        const categoryIds = category.generators.map(g => g.id);
        setSelectedGenerators(prev => prev.filter(id => !categoryIds.includes(id)));
      }
    } else {
      setSelectedGenerators([]);
    }
  };

  const activeCategoryData = categories.find(c => c.id === activeCategory) || categories[0];
  const activeGenerators = activeCategoryData.generators;
  const selectedInCategory = activeGenerators.filter(g => selectedGenerators.includes(g.id)).length;

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
              Onboarding Data Generation
            </h2>
            <p
              className={`text-sm ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}
            >
              Generate comprehensive onboarding documentation and training materials
            </p>
          </div>
        </div>

        {/* STATUS CARD */}
        <div
          className={`p-6 rounded-lg border transition-all mb-6 ${
            onboardingStatus === "completed"
              ? darkMode
                ? "border-green-700 bg-green-900/20"
                : "border-emerald-200 bg-emerald-50"
              : onboardingStatus === "running"
              ? darkMode
                ? "border-blue-700 bg-blue-900/20 ring-2 ring-blue-800"
                : "border-sky-200 bg-sky-50 ring-2 ring-sky-200"
              : onboardingStatus === "error"
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
              {getStepIcon(onboardingStatus)}
              <div>
                <h3
                  className={`text-lg font-semibold ${
                    darkMode ? "text-white" : "text-slate-900"
                  }`}
                >
                  Onboarding Generation Status
                </h3>
                <p
                  className={`text-sm ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`}
                >
                  {onboardingStatus === "pending" && "Ready to generate onboarding data"}
                  {onboardingStatus === "running" && "Generating onboarding documentation..."}
                  {onboardingStatus === "completed" && "Onboarding data generated successfully"}
                  {onboardingStatus === "error" && "Generation failed"}
                </p>
              </div>
            </div>

            <button
              onClick={() => onRunOnboarding(selectedGenerators)}
              disabled={onboardingRunning || selectedGenerators.length === 0}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                onboardingRunning || selectedGenerators.length === 0
                  ? darkMode
                    ? "bg-gray-600 cursor-not-allowed"
                    : "bg-slate-200 text-slate-500 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white"
              } shadow-md hover:shadow-lg disabled:shadow-none`}
            >
              {onboardingRunning ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </span>
              ) : (
                `Generate Onboarding Data (${selectedGenerators.length} selected)`
              )}
            </button>
          </div>

          {/* MESSAGE */}
          {onboardingMessage && (
            <div
              className={`mt-4 p-3 rounded-lg text-sm ${
                onboardingStatus === "completed"
                  ? darkMode
                    ? "bg-green-900/30 text-green-300"
                    : "bg-emerald-100 text-emerald-700"
                  : onboardingStatus === "error"
                  ? darkMode
                    ? "bg-red-900/30 text-red-300"
                    : "bg-rose-100 text-rose-700"
                  : darkMode
                  ? "bg-blue-900/30 text-blue-300"
                  : "bg-sky-100 text-sky-700"
              }`}
            >
              {onboardingMessage}
            </div>
          )}
        </div>

        {/* CATEGORY TABS */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3
                className={`text-lg font-semibold mb-1 ${
                  darkMode ? "text-white" : "text-slate-900"
                }`}
              >
                Select Generators
              </h3>
              <p
                className={`text-sm ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}
              >
                Choose which documentation types to generate ({selectedGenerators.length}/{allGenerators.length} selected)
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => selectAllGenerators(activeCategory)}
                className={`px-3 py-1.5 text-xs rounded-md transition ${
                  darkMode
                    ? "bg-gray-700 hover:bg-gray-600 text-gray-300"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                }`}
              >
                Select All ({activeCategoryData.name})
              </button>
              <button
                onClick={() => deselectAllGenerators(activeCategory)}
                className={`px-3 py-1.5 text-xs rounded-md transition ${
                  darkMode
                    ? "bg-gray-700 hover:bg-gray-600 text-gray-300"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                }`}
              >
                Deselect All ({activeCategoryData.name})
              </button>
            </div>
          </div>

          {/* TABS */}
          <div className="flex gap-2 mb-4 border-b border-gray-300 dark:border-gray-700">
            {categories.map((category) => {
              const CategoryIcon = category.icon;
              const isActive = activeCategory === category.id;
              const categorySelectedCount = category.generators.filter(g => 
                selectedGenerators.includes(g.id)
              ).length;
              
              return (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`flex items-center gap-2 px-4 py-2 font-medium transition-all border-b-2 ${
                    isActive
                      ? darkMode
                        ? "border-blue-500 text-blue-400"
                        : "border-blue-500 text-blue-600"
                      : darkMode
                      ? "border-transparent text-gray-400 hover:text-gray-300"
                      : "border-transparent text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <CategoryIcon className="w-4 h-4" />
                  <span>{category.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    isActive
                      ? darkMode
                        ? "bg-blue-900/30 text-blue-300"
                        : "bg-blue-100 text-blue-700"
                      : darkMode
                      ? "bg-gray-700 text-gray-400"
                      : "bg-slate-200 text-slate-600"
                  }`}>
                    {categorySelectedCount}/{category.generators.length}
                  </span>
                </button>
              );
            })}
          </div>

          {/* GENERATORS FOR ACTIVE CATEGORY */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeGenerators.map((generator) => {
              const Icon = generator.icon;
              const isSelected = selectedGenerators.includes(generator.id);
              
              return (
                <div
                  key={generator.id}
                  onClick={() => toggleGenerator(generator.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    isSelected
                      ? darkMode
                        ? "border-blue-500 bg-blue-900/20"
                        : "border-blue-500 bg-blue-50"
                      : darkMode
                      ? "border-gray-700 bg-gray-800/50 hover:border-gray-600"
                      : "border-slate-200 bg-slate-50 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        isSelected
                          ? darkMode
                            ? "bg-blue-700/50"
                            : "bg-blue-100"
                          : darkMode
                          ? "bg-gray-700"
                          : "bg-slate-200"
                      }`}
                    >
                      <Icon
                        className={`w-5 h-5 ${
                          isSelected
                            ? "text-blue-600 dark:text-blue-400"
                            : darkMode
                            ? "text-gray-400"
                            : "text-slate-600"
                        }`}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h4
                          className={`font-semibold ${
                            darkMode ? "text-white" : "text-slate-900"
                          }`}
                        >
                          {generator.name}
                        </h4>
                        {isSelected && (
                          <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        )}
                      </div>
                      <p
                        className={`text-xs mb-2 ${
                          darkMode ? "text-gray-400" : "text-slate-600"
                        }`}
                      >
                        {generator.description}
                      </p>
                      <div className="flex items-center gap-1.5">
                        <FileText className={`w-3 h-3 ${
                          darkMode ? "text-gray-500" : "text-slate-400"
                        }`} />
                        <span className={`text-xs ${
                          darkMode ? "text-gray-500" : "text-slate-500"
                        }`}>
                          {generator.outputFile}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* INFO SECTION */}
        <div
          className={`p-4 rounded-lg border ${
            darkMode
              ? "bg-blue-900/10 border-blue-800"
              : "bg-blue-50 border-blue-200"
          }`}
        >
          <div className="flex items-start gap-3">
            <Info className={`w-5 h-5 mt-0.5 ${
              darkMode ? "text-blue-400" : "text-blue-600"
            }`} />
            <div className="flex-1">
              <h4
                className={`font-semibold mb-1 ${
                  darkMode ? "text-blue-300" : "text-blue-900"
                }`}
              >
                About Onboarding Generation
              </h4>
              <ul className={`text-sm space-y-1 ${
                darkMode ? "text-blue-200" : "text-blue-800"
              }`}>
                <li>• Generated files are saved in separate directories:</li>
                {categories.map(category => (
                  <li key={category.id} className="ml-4">
                    - <code className="px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30">backend/data/Onboarding/{category.outputDir}/</code> ({category.name})
                  </li>
                ))}
                <li>• All generators use the existing vector database for context</li>
                <li>• Generation may take several minutes depending on repository size</li>
                <li>• Each generator creates a separate JSON file with structured documentation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* OUTPUT FILES SECTION */}
      {onboardingStatus === "completed" && (
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
          {categories.map((category) => {
            const categoryGenerators = category.generators.filter(g => 
              selectedGenerators.includes(g.id)
            );
            
            if (categoryGenerators.length === 0) return null;
            
            const CategoryIcon = category.icon;
            
            return (
              <div key={category.id} className="mb-6 last:mb-0">
                <div className="flex items-center gap-2 mb-3">
                  <CategoryIcon className={`w-5 h-5 ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`} />
                  <h4
                    className={`text-lg font-semibold ${
                      darkMode ? "text-white" : "text-slate-900"
                    }`}
                  >
                    {category.name}
                  </h4>
                  <span className={`text-xs px-2 py-1 rounded ${
                    darkMode
                      ? "bg-gray-700 text-gray-300"
                      : "bg-slate-200 text-slate-600"
                  }`}>
                    {category.outputDir}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {categoryGenerators.map((generator) => {
                    const Icon = generator.icon;
                    return (
                      <div
                        key={generator.id}
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
                          <span className={`text-sm font-medium ${
                            darkMode ? "text-white" : "text-slate-900"
                          }`}>
                            {generator.name}
                          </span>
                        </div>
                        <p className={`text-xs ${
                          darkMode ? "text-gray-400" : "text-slate-600"
                        }`}>
                          {generator.outputFile}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

