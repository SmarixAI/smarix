"use client";

import { useState, useEffect } from "react";
import { Loader2, FileText, CheckCircle2, AlertCircle, FolderOpen, BookOpen, Code, Settings, Layers, Bug, GraduationCap, MessageSquare } from "lucide-react";
import { StepStatus } from "./types";
import { getStepIcon } from "./StepCard";
import { Space_Grotesk, Fira_Code } from 'next/font/google';
import Image from 'next/image';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const firaCode = Fira_Code({ subsets: ['latin'] });

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
                  Onboarding Data Generation
                </h2>
                <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}>
                  Generate comprehensive onboarding documentation and training materials
                </p>
              </div>
            </div>
          </div>

          {/* STATUS CARD */}
          <div
            className={`p-6 rounded-xl border transition-all mb-6 backdrop-blur-sm ${
              onboardingStatus === "completed"
                ? "border-emerald-200/50 bg-emerald-50/80"
                : onboardingStatus === "running"
                ? "border-sky-200/50 bg-sky-50/80 ring-2 ring-sky-200/30"
                : onboardingStatus === "error"
                ? "border-rose-200/50 bg-rose-50/80"
                : "border-gray-200/50 bg-gray-50/80"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStepIcon(onboardingStatus)}
                <div>
                  <h3 className={`${spaceGrotesk.className} text-lg font-semibold text-[#0E1B2E]`}>
                    Onboarding Generation Status
                  </h3>
                  <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}>
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
                className={`${spaceGrotesk.className} px-6 py-2.5 rounded-xl font-medium transition-all ${
                  onboardingRunning || selectedGenerators.length === 0
                    ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                    : "bg-[#0E1B2E] hover:bg-[#0E1B2E]/90 text-white shadow-lg shadow-[#0E1B2E]/20 hover:shadow-xl hover:shadow-[#0E1B2E]/30"
                } disabled:shadow-none`}
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
                className={`mt-4 p-3 rounded-lg text-sm ${firaCode.className} ${
                  onboardingStatus === "completed"
                    ? "bg-emerald-100/80 text-emerald-700 border border-emerald-200/50"
                    : onboardingStatus === "error"
                    ? "bg-rose-100/80 text-rose-700 border border-rose-200/50"
                    : "bg-sky-100/80 text-sky-700 border border-sky-200/50"
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
                <h3 className={`${spaceGrotesk.className} text-lg font-semibold mb-1 text-[#0E1B2E]`}>
                  Select Generators
                </h3>
                <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}>
                  Choose which documentation types to generate ({selectedGenerators.length}/{allGenerators.length} selected)
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => selectAllGenerators(activeCategory)}
                  className={`${spaceGrotesk.className} px-3 py-1.5 text-xs rounded-lg transition bg-white/80 hover:bg-[#0E1B2E]/5 text-[#0E1B2E]/70 hover:text-[#0E1B2E] border border-gray-200/50`}
                >
                  Select All ({activeCategoryData.name})
                </button>
                <button
                  onClick={() => deselectAllGenerators(activeCategory)}
                  className={`${spaceGrotesk.className} px-3 py-1.5 text-xs rounded-lg transition bg-white/80 hover:bg-[#0E1B2E]/5 text-[#0E1B2E]/70 hover:text-[#0E1B2E] border border-gray-200/50`}
                >
                  Deselect All ({activeCategoryData.name})
                </button>
              </div>
            </div>

            {/* TABS */}
            <div className="flex gap-2 mb-4 border-b border-gray-200/50">
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
                  className={`${spaceGrotesk.className} flex items-center gap-2 px-4 py-2 font-medium transition-all border-b-2 ${
                    isActive
                      ? "border-[#0E1B2E] text-[#0E1B2E]"
                      : "border-transparent text-[#0E1B2E]/60 hover:text-[#0E1B2E]"
                  }`}
                >
                  <CategoryIcon className="w-4 h-4" />
                  <span>{category.name}</span>
                  <span className={`${firaCode.className} text-xs px-1.5 py-0.5 rounded ${
                    isActive
                      ? "bg-[#0E1B2E]/10 text-[#0E1B2E]"
                      : "bg-gray-100 text-[#0E1B2E]/60"
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
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all backdrop-blur-sm ${
                      isSelected
                        ? "border-[#0E1B2E] bg-[#0E1B2E]/5 shadow-lg shadow-[#0E1B2E]/10"
                        : "border-gray-200/50 bg-white/50 hover:border-[#0E1B2E]/30 hover:bg-[#0E1B2E]/5"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`p-2 rounded-lg ${
                          isSelected
                            ? "bg-[#0E1B2E]"
                            : "bg-gray-100"
                        }`}
                      >
                        <Icon
                          className={`w-5 h-5 ${
                            isSelected
                              ? "text-white"
                              : "text-[#0E1B2E]/60"
                          }`}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className={`${spaceGrotesk.className} font-semibold text-[#0E1B2E]`}>
                            {generator.name}
                          </h4>
                          {isSelected && (
                            <CheckCircle2 className="w-5 h-5 text-[#0E1B2E]" />
                          )}
                        </div>
                        <p className={`${firaCode.className} text-xs mb-2 text-[#0E1B2E]/60`}>
                          {generator.description}
                        </p>
                        <div className="flex items-center gap-1.5">
                          <FileText className="w-3 h-3 text-[#0E1B2E]/40" />
                          <span className={`${firaCode.className} text-xs text-[#0E1B2E]/50`}>
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
        </div>
      </div>
    </div>
  );
}

