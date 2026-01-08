"use client";

import {
  X,
  BookOpen,
  FileText,
  Clock,
  Award,
  ChevronDown,
  Loader2,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  CheckCircle2,
  XCircle,
  Send,
} from "lucide-react";
import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { ContentParser } from "../../utils/ReadingOverview/contentParser";
import { MermaidRenderer } from "../../utils/ReadingOverview/mermaidRenderer";
import ContentRenderer from "./ContentRenderer";
import { ContentService } from "../../services/ReadingOverview/contentService";
import { QAService } from "../../services/QASession/contentService";
import type { ModuleContent, QuestionData } from "../../../../../types/onboarding";

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
  title: string;
  moduleId: string;
  activeRepos?: string[];
}

interface ModuleWithContent {
  moduleId: string;
  moduleTitle: string;
  jsonFile: string;
  content: ModuleContent | null;
  sections: any[];
  isQnASection?: boolean;
  questions?: QuestionData[];
}

// Mapping from ReadingOverview module IDs to QA module IDs
const MODULE_ID_TO_QA_ID: { [key: string]: string } = {
  '1': 'overview',           // Project Overview
  '2': 'tech_stack',         // Tech Stacks
  '3': 'repo_structure',     // Repo Structure
  '4': 'app_features',       // App Features
  '5': 'dev_setup',          // Dev Setup
  '6': 'code_conventions',   // Code Conventions
};

export default function OverviewModal({
  isOpen,
  onClose,
  darkMode,
  title,
  moduleId,
  activeRepos = [],
}: ContentModalProps) {
  const [moduleContent, setModuleContent] = useState<ModuleWithContent[]>([]);
  const [renderedMermaid, setRenderedMermaid] = useState<{
    [key: string]: { [key: number]: string };
  }>({});
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: string]: string }>({});
  const [submittedAnswers, setSubmittedAnswers] = useState<{ [key: string]: string }>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showQnA, setShowQnA] = useState(false);
  const [qaData, setQaData] = useState<{ questions: QuestionData[]; moduleTitle: string } | null>(null);
  const [isLoadingQnA, setIsLoadingQnA] = useState(false);
  
  const scrollTimeoutRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const activeReposRef = useRef<string[]>([]);

  useEffect(() => {
    if (isOpen && moduleId) {
      setIsLoading(true);
      MermaidRenderer.initialize(darkMode);
      document.body.style.overflow = "hidden";

      const fetchModuleContent = async () => {
        try {
          const content: ModuleWithContent[] = [];
          const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
          activeReposRef.current = activeRepos;
          
          // Fetch reading content
          const response = await ContentService.fetchModuleContent(moduleId, repo);

          if (response && response.sections) {
            response.sections.forEach((section) => {
              content.push({
                moduleId: section.sectionId,
                moduleTitle: section.sectionTitle,
                jsonFile: response.jsonFile,
                content: section.content,
                sections: section.content?.answer
                  ? ContentParser.parseContent(section.content.answer)
                  : [],
                isQnASection: false,
              });
            });
          }

          // QnA will be fetched separately when "Start QnA" button is clicked

          // Set content immediately to show it, don't wait for mermaid
          setModuleContent(content);
          setCurrentSectionIndex(0); // Reset to first section when new content loads
          setIsLoading(false);
        } catch (error) {
          console.error("Error fetching module content:", error);
          setIsLoading(false);
        }
      };

      fetchModuleContent();
    } else {
      document.body.style.overflow = "unset";
      setModuleContent([]);
      setRenderedMermaid({});
      setScrollProgress(0);
      setCurrentSectionIndex(0);
      setSelectedAnswers({});
      setSubmittedAnswers({});
      setIsSubmitted(false);
      setShowQnA(false);
      setQaData(null);
    }

    return () => {
      document.body.style.overflow = "unset";
      if (scrollTimeoutRef.current) {
        cancelAnimationFrame(scrollTimeoutRef.current);
      }
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isOpen, moduleId, darkMode, activeRepos]);

  useEffect(() => {
    if (isOpen && moduleContent.length > 0) {
      // Render mermaid diagrams asynchronously without blocking UI
      const renderAllMermaid = async () => {
        const mermaidByModule: { [key: string]: { [key: number]: string } } = {};

        // Process mermaid rendering in batches to avoid blocking
        for (const moduleData of moduleContent) {
          if (moduleData.content?.answer) {
            const mermaidDiagrams = ContentParser.extractMermaidDiagrams(
              moduleData.content.answer
            );

            if (mermaidDiagrams.length > 0) {
              try {
                const results = await MermaidRenderer.renderMultiple(mermaidDiagrams);
                const mermaidMap: { [key: number]: string } = {};
                results.forEach((svg, index) => {
                  if (svg) mermaidMap[index] = svg;
                });
                mermaidByModule[moduleData.moduleId] = mermaidMap;
              } catch (error) {
                console.error("Error rendering mermaid:", error);
              }
            }
          }
        }

        // Update state once with all rendered mermaid diagrams
        setRenderedMermaid(mermaidByModule);
      };

      // Use requestIdleCallback or setTimeout to defer mermaid rendering
      if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
        requestIdleCallback(renderAllMermaid, { timeout: 1000 });
      } else {
        setTimeout(renderAllMermaid, 0);
      }
    }
  }, [isOpen, moduleContent]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      const target = e.target as HTMLDivElement;
      const scrollHeight = target.scrollHeight - target.clientHeight;
      const progress = scrollHeight > 0 ? (target.scrollTop / scrollHeight) * 100 : 0;
      setScrollProgress(Math.min(100, Math.max(0, progress)));
    });
  }, []);

  const toggleModuleExpanded = useCallback((moduleId: string) => {
    setExpandedModules((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(moduleId)) {
        newSet.delete(moduleId);
      } else {
        newSet.add(moduleId);
      }
      return newSet;
    });
  }, []);

  const handleNextSection = useCallback(() => {
    setCurrentSectionIndex((prev) => {
      if (prev < moduleContent.length - 1) {
        return prev + 1;
      }
      return prev;
    });
  }, [moduleContent.length]);

  const handlePreviousSection = useCallback(() => {
    setCurrentSectionIndex((prev) => {
      if (prev > 0) {
        return prev - 1;
      }
      return prev;
    });
  }, []);

  const handleAnswerSelect = useCallback((questionKey: string, option: string) => {
    if (isSubmitted) return;
    
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionKey]: option,
    }));
  }, [isSubmitted]);

  const handleSubmitQnA = useCallback(() => {
    setSubmittedAnswers(selectedAnswers);
    setIsSubmitted(true);
  }, [selectedAnswers]);

  const handleResetQnA = useCallback(() => {
    setSelectedAnswers({});
    setSubmittedAnswers({});
    setIsSubmitted(false);
  }, []);

  const handleStartQnA = useCallback(async () => {
    setIsLoadingQnA(true);
    const repo = activeReposRef.current.length > 0 ? activeReposRef.current[0] : undefined;
    const qaModuleId = MODULE_ID_TO_QA_ID[moduleId];
    
    if (qaModuleId) {
      try {
        const qaResponse = await QAService.fetchQAModule(qaModuleId, repo);
        if (qaResponse && qaResponse.questions && qaResponse.questions.length > 0) {
          setQaData({
            questions: qaResponse.questions,
            moduleTitle: title
          });
          setShowQnA(true);
        }
      } catch (qaError) {
        console.error("Error fetching Q&A data:", qaError);
      }
    }
    setIsLoadingQnA(false);
  }, [moduleId, title]);

  const handleBackToContent = useCallback(() => {
    setShowQnA(false);
    setSelectedAnswers({});
    setSubmittedAnswers({});
    setIsSubmitted(false);
  }, []);

  const handleBackdropClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  const stats = useMemo(() => {
    const totalWords = moduleContent.reduce(
      (sum, mod) => sum + (mod.content?.answer?.length || 0),
      0
    );
    const estimatedReadTime = Math.ceil(totalWords / 1000);
    const totalSections = moduleContent.reduce(
      (sum, mod) => sum + mod.sections.length,
      0
    );
    return { estimatedReadTime, totalSections };
  }, [moduleContent]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={handleBackdropClick}
    >
      <style jsx global>{`
        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: scale(0.98);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes backdropFade {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fadeIn 0.3s ease-out;
        }

        .modal-backdrop {
          animation: backdropFade 0.3s ease-out;
        }

        .modal-content {
          animation: modalSlideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
          will-change: transform, opacity;
        }

        .shimmer-background {
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
          background-size: 200% 100%;
          animation: shimmer 3s infinite;
        }

        .floating-icon {
          animation: float 3s ease-in-out infinite;
        }

        .custom-scrollbar {
          will-change: scroll-position;
          transform: translateZ(0);
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 10px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: ${darkMode ? "#1f2937" : "#f1f5f9"};
          border-radius: 10px;
          margin: 8px 0;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: ${darkMode
            ? "linear-gradient(180deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)"
            : "linear-gradient(180deg, #6366f1 0%, #06b6d4 50%, #14b8a6 100%)"};
          border-radius: 10px;
          border: 2px solid ${darkMode ? "#1f2937" : "#f1f5f9"};
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${darkMode
            ? "linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)"
            : "linear-gradient(180deg, #4f46e5 0%, #0891b2 50%, #0d9488 100%)"};
        }
      `}</style>

      <div
        className={`absolute inset-0 modal-backdrop ${
          darkMode
            ? "bg-gradient-to-br from-gray-900/95 via-blue-900/90 to-purple-900/95"
            : "bg-gradient-to-br from-slate-900/60 via-indigo-900/50 to-cyan-900/60"
        } backdrop-blur-xl`}
      />

      <div
        className={`relative w-full h-full overflow-hidden modal-content ${
          darkMode ? "glass-card-dark" : "glass-card-light"
        }`}
        style={{
          boxShadow: darkMode
            ? "0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)"
            : "0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-1 z-20 bg-gray-700/30">
          <div
            className={`h-full transition-all duration-300 ${
              darkMode
                ? "bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                : "bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500"
            }`}
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        <div
          className={`sticky top-0 z-10 px-16 py-5 border-b backdrop-blur-2xl ${
            darkMode
              ? "bg-gray-800/98 border-gray-700/50"
              : "bg-white/98 border-indigo-100/50"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 flex-1">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-2xl floating-icon relative overflow-hidden ${
                  darkMode
                    ? "bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600"
                    : "bg-gradient-to-br from-indigo-500 via-cyan-500 to-teal-500"
                }`}
              >
                <div className="absolute inset-0 shimmer-background" />
                <BookOpen className="w-6 h-6 text-white relative z-10" />
              </div>

              <div className="flex items-center space-x-6">
                <h2
                  className={`text-3xl font-bold ${
                    darkMode
                      ? "bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent"
                      : "bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent"
                  }`}
                >
                  {title}
                </h2>

                <div className="flex items-center space-x-4">
                  <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${
                    darkMode ? "bg-blue-500/10" : "bg-indigo-50"
                  }`}>
                    <Clock className={`w-4 h-4 ${darkMode ? "text-blue-400" : "text-indigo-500"}`} />
                    <span className={`text-xs font-medium ${
                      darkMode ? "text-blue-300" : "text-indigo-700"
                    }`}>
                      {stats.estimatedReadTime} min read
                    </span>
                  </div>

                  <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${
                    darkMode ? "bg-purple-500/10" : "bg-purple-50"
                  }`}>
                    <FileText className={`w-4 h-4 ${darkMode ? "text-purple-400" : "text-purple-500"}`} />
                    <span className={`text-xs font-medium ${
                      darkMode ? "text-purple-300" : "text-purple-700"
                    }`}>
                      Section {currentSectionIndex + 1} of {moduleContent.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className={`p-3 rounded-xl transition-all duration-300 hover:rotate-90 hover:scale-110 group ${
                darkMode ? "hover:bg-gray-700" : "hover:bg-indigo-50"
              }`}
              aria-label="Close modal"
            >
              <X
                className={`w-6 h-6 transition-colors ${
                  darkMode
                    ? "text-gray-400 group-hover:text-white"
                    : "text-slate-500 group-hover:text-slate-900"
                }`}
              />
            </button>
          </div>
        </div>

        <div
          className="overflow-y-auto custom-scrollbar"
          style={{
            height: "calc(100vh - 100px)",
          }}
          onScroll={handleScroll}
        >
          <div className="w-full px-16 py-10">
          {isLoading && moduleContent.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32">
              <div className="relative">
                <Loader2 className={`w-16 h-16 animate-spin ${
                  darkMode ? "text-blue-400" : "text-indigo-600"
                }`} />
              </div>
              <p className={`mt-4 text-sm font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Loading module...
              </p>
            </div>
          ) : moduleContent.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32">
              <p className={`text-lg font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                No content found
              </p>
            </div>
          ) : showQnA && qaData ? (
            /* Exam-Style QnA View */
            <div className="flex flex-col h-full">
              {/* Exam Header */}
              <div className={`mb-6 p-6 rounded-2xl border-2 ${
                darkMode
                  ? "bg-gray-800/80 border-purple-500/50"
                  : "bg-white border-purple-300"
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className={`text-2xl font-bold mb-2 ${
                      darkMode ? "text-white" : "text-slate-900"
                    }`}>
                      📝 Knowledge Assessment
                    </h2>
                    <p className={`text-sm ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}>
                      {qaData.moduleTitle} - Test your understanding
                    </p>
                  </div>
                  <div className={`px-4 py-2 rounded-lg ${
                    darkMode ? "bg-purple-500/20" : "bg-purple-100"
                  }`}>
                    <span className={`text-sm font-semibold ${
                      darkMode ? "text-purple-300" : "text-purple-700"
                    }`}>
                      {qaData.questions.length} Questions
                    </span>
                  </div>
                </div>
                
                {!isSubmitted && (
                  <div className={`flex items-center gap-2 text-sm ${
                    darkMode ? "text-yellow-400" : "text-amber-600"
                  }`}>
                    <Clock className="w-4 h-4" />
                    <span>Take your time to answer all questions</span>
                  </div>
                )}
              </div>

              {/* Questions */}
              <div className="flex-1 overflow-y-auto space-y-6">
                {qaData.questions.map((question) => {
                  const qKey = `qa-${question.question_number}`;
                  const selectedOption = selectedAnswers[qKey];
                  const submittedOption = submittedAnswers[qKey];
                  const isCorrect = submittedOption === question.correct_answer;

                  return (
                    <div
                      key={question.question_number}
                      className={`p-6 rounded-xl border-2 ${
                        darkMode
                          ? "bg-gray-800/50 border-gray-700"
                          : "bg-white border-slate-200"
                      }`}
                    >
                      <div className="flex items-start gap-4 mb-4">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold flex-shrink-0 ${
                          darkMode ? "bg-purple-600 text-white" : "bg-purple-500 text-white"
                        }`}>
                          {question.question_number}
                        </div>
                        <p className={`font-semibold text-lg flex-1 ${
                          darkMode ? "text-white" : "text-slate-900"
                        }`}>
                          {question.question}
                        </p>
                      </div>

                      <div className="ml-12 space-y-3">
                        {Object.entries(question.options).map(([optKey, optText]) => {
                          const isSelected = selectedOption === optKey;
                          const isCorrectOption = optKey === question.correct_answer;
                          const showCorrect = isSubmitted && isCorrectOption;
                          const showWrong = isSubmitted && submittedOption === optKey && !isCorrect;

                          return (
                            <button
                              key={optKey}
                              onClick={() => handleAnswerSelect(qKey, optKey)}
                              disabled={isSubmitted}
                              className={`w-full text-left px-5 py-4 rounded-lg border-2 text-sm transition-all ${
                                showCorrect
                                  ? darkMode
                                    ? "bg-green-600/30 border-green-400 text-green-200"
                                    : "bg-green-100 border-green-500 text-green-900"
                                  : showWrong
                                  ? darkMode
                                    ? "bg-red-600/30 border-red-400 text-red-200"
                                    : "bg-red-100 border-red-500 text-red-900"
                                  : isSelected
                                  ? darkMode
                                    ? "bg-blue-600/40 border-blue-400 text-white"
                                    : "bg-blue-100 border-blue-500 text-slate-900"
                                  : darkMode
                                  ? "bg-gray-700/50 border-gray-600 text-gray-200 hover:bg-gray-700/70"
                                  : "bg-slate-50 border-slate-300 text-slate-700 hover:bg-blue-50"
                              } ${isSubmitted ? "cursor-not-allowed" : "cursor-pointer"}`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium">
                                  <strong>{optKey}.</strong> {optText as string}
                                </span>
                                {showCorrect && <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />}
                                {showWrong && <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                              </div>
                            </button>
                          );
                        })}
                      </div>

                      {isSubmitted && (
                        <div className={`mt-4 ml-12 p-4 rounded-lg border ${
                          darkMode
                            ? "bg-gray-900/50 text-gray-200 border-gray-700"
                            : "bg-slate-50 text-slate-800 border-slate-200"
                        }`}
                        >
                          <p className={`font-semibold mb-2 ${
                            darkMode ? "text-green-300" : "text-green-700"
                          }`}>
                            Correct Answer: <strong>{question.correct_answer}</strong>
                          </p>
                          <p className="text-sm leading-relaxed">{question.explanation}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Submit Button */}
              {!isSubmitted && (
                <div className="mt-6 flex justify-center">
                  <button
                    onClick={handleSubmitQnA}
                    disabled={Object.keys(selectedAnswers).length === 0}
                    className={`px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 active:scale-95 shadow-2xl flex items-center space-x-3 ${
                      Object.keys(selectedAnswers).length === 0
                        ? darkMode
                          ? "bg-gray-700/50 text-gray-500 cursor-not-allowed"
                          : "bg-slate-200 text-slate-400 cursor-not-allowed"
                        : darkMode
                        ? "bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 hover:from-purple-500 hover:via-pink-500 hover:to-red-500 text-white"
                        : "bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 hover:from-purple-600 hover:via-pink-600 hover:to-red-600 text-white"
                    }`}
                  >
                    <Send className="w-6 h-6" />
                    <span>Submit Answers</span>
                  </button>
                </div>
              )}

              {/* Back to Content Button */}
              <div className="mt-4 flex justify-center">
                <button
                  onClick={handleBackToContent}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                    darkMode
                      ? "bg-gray-700 text-gray-200 hover:bg-gray-600"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  ← Back to Content
                </button>
              </div>
            </div>
          ) : moduleContent.length > 0 && currentSectionIndex < moduleContent.length ? (
            <div className="flex flex-col h-full">
              {/* Current Section Display */}
              <div className="flex-1">
                {(() => {
                  const moduleData = moduleContent[currentSectionIndex];
                  const isLastSection = currentSectionIndex === moduleContent.length - 1;
                  return (
                    <div
                      key={moduleData.moduleId}
                      id={`module-section-${moduleData.moduleId}`}
                      className={`rounded-2xl overflow-hidden transition-all animate-fade-in ${
                        darkMode
                          ? "bg-gray-800/50 ring-1 ring-gray-700"
                          : "bg-white/50 ring-1 ring-slate-200"
                      }`}
                    >
                      <div
                        className={`px-8 py-5 border-b ${
                          darkMode
                            ? "bg-gray-800/80 border-gray-700"
                            : "bg-slate-50/80 border-slate-200"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span
                              className={`text-2xl font-bold ${
                                darkMode ? "text-blue-400" : "text-indigo-600"
                              }`}
                            >
                              {currentSectionIndex + 1}.
                            </span>
                            <h3
                              className={`text-xl font-bold ${
                                darkMode ? "text-gray-100" : "text-slate-900"
                              }`}
                            >
                              {moduleData.moduleTitle}
                            </h3>
                          </div>

                          {!moduleData.isQnASection && moduleData.content?.quality && (
                            <div
                              className={`flex items-center space-x-1 px-3 py-1 rounded-lg ${
                                darkMode ? "bg-yellow-500/10" : "bg-amber-50"
                              }`}
                            >
                              <Award
                                className={`w-3 h-3 ${
                                  darkMode ? "text-yellow-400" : "text-amber-500"
                                }`}
                              />
                              <span
                                className={`text-xs font-semibold ${
                                  darkMode ? "text-yellow-300" : "text-amber-700"
                                }`}
                              >
                                {(moduleData.content.quality * 5).toFixed(1)}
                              </span>
                            </div>
                          )}

                          {moduleData.isQnASection && moduleData.questions && (
                            <div
                              className={`flex items-center space-x-1 px-3 py-1 rounded-lg ${
                                darkMode ? "bg-purple-500/10" : "bg-purple-50"
                              }`}
                            >
                              <MessageSquare
                                className={`w-3 h-3 ${
                                  darkMode ? "text-purple-400" : "text-purple-500"
                                }`}
                              />
                              <span
                                className={`text-xs font-semibold ${
                                  darkMode ? "text-purple-300" : "text-purple-700"
                                }`}
                              >
                                {moduleData.questions.length} Questions
                              </span>
                            </div>
                          )}
                        </div>

                        {moduleData.content?.question && (
                          <div className="mt-3">
                            <button
                              onClick={() => toggleModuleExpanded(moduleData.moduleId)}
                              className={`w-full text-left text-sm ${
                                darkMode ? "text-gray-400" : "text-slate-600"
                              } hover:${
                                darkMode ? "text-gray-300" : "text-slate-700"
                              } transition-colors flex items-center space-x-2`}
                            >
                              <ChevronDown
                                className={`w-4 h-4 transition-transform ${
                                  expandedModules.has(moduleData.moduleId) ? "rotate-180" : ""
                                }`}
                              />
                              <span className="font-medium">Learning Objective</span>
                            </button>

                            {expandedModules.has(moduleData.moduleId) && (
                              <p
                                className={`mt-2 text-sm leading-relaxed ${
                                  darkMode ? "text-gray-400" : "text-slate-600"
                                }`}
                              >
                                {moduleData.content.question}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="px-8 py-8">
                        <ContentRenderer
                          sections={moduleData.sections}
                          darkMode={darkMode}
                          renderedMermaid={renderedMermaid[moduleData.moduleId] || {}}
                        />
                        
                        {/* Show Start QnA button after last section */}
                        {isLastSection && (
                          <div className="mt-12 pt-8 border-t border-gray-700">
                            <div className={`p-8 rounded-2xl border-2 text-center ${
                              darkMode
                                ? "bg-gradient-to-br from-purple-900/30 to-pink-900/30 border-purple-500/50"
                                : "bg-gradient-to-br from-purple-50 to-pink-50 border-purple-300"
                            }`}>
                              <MessageSquare className={`w-16 h-16 mx-auto mb-4 ${
                                darkMode ? "text-purple-400" : "text-purple-600"
                              }`} />
                              <h3 className={`text-2xl font-bold mb-2 ${
                                darkMode ? "text-white" : "text-slate-900"
                              }`}>
                                Ready for Assessment?
                              </h3>
                              <p className={`text-sm mb-6 ${
                                darkMode ? "text-gray-400" : "text-slate-600"
                              }`}>
                                Test your understanding with a knowledge check quiz
                              </p>
                              <button
                                onClick={handleStartQnA}
                                disabled={isLoadingQnA}
                                className={`px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 active:scale-95 shadow-2xl flex items-center space-x-3 mx-auto ${
                                  isLoadingQnA
                                    ? darkMode
                                      ? "bg-gray-700/50 text-gray-500 cursor-not-allowed"
                                      : "bg-slate-200 text-slate-400 cursor-not-allowed"
                                    : darkMode
                                    ? "bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 hover:from-purple-500 hover:via-pink-500 hover:to-red-500 text-white"
                                    : "bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 hover:from-purple-600 hover:via-pink-600 hover:to-red-600 text-white"
                                }`}
                              >
                                {isLoadingQnA ? (
                                  <>
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                    <span>Loading...</span>
                                  </>
                                ) : (
                                  <>
                                    <MessageSquare className="w-6 h-6" />
                                    <span>Start QnA Assessment</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Navigation Buttons */}
              <div className={`mt-8 flex items-center justify-between pt-6 border-t ${
                darkMode ? "border-gray-700" : "border-slate-200"
              }`}>
                <button
                  onClick={handlePreviousSection}
                  disabled={currentSectionIndex === 0}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                    currentSectionIndex === 0
                      ? darkMode
                        ? "bg-gray-700/50 text-gray-500 cursor-not-allowed"
                        : "bg-slate-200 text-slate-400 cursor-not-allowed"
                      : darkMode
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-500 hover:to-purple-500 hover:shadow-lg"
                      : "bg-gradient-to-r from-indigo-500 to-cyan-500 text-white hover:from-indigo-600 hover:to-cyan-600 hover:shadow-lg"
                  }`}
                >
                  <ChevronLeft className="w-5 h-5" />
                  <span>Previous</span>
                </button>

                {/* Progress Dots */}
                <div className="flex items-center space-x-2">
                  {moduleContent.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSectionIndex(index)}
                      className={`w-2 h-2 rounded-full transition-all duration-300 ${
                        index === currentSectionIndex
                          ? darkMode
                            ? "bg-blue-400 w-8"
                            : "bg-indigo-600 w-8"
                          : darkMode
                          ? "bg-gray-600 hover:bg-gray-500"
                          : "bg-slate-300 hover:bg-slate-400"
                      }`}
                      aria-label={`Go to section ${index + 1}`}
                    />
                  ))}
                </div>

                <button
                  onClick={handleNextSection}
                  disabled={currentSectionIndex === moduleContent.length - 1}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                    currentSectionIndex === moduleContent.length - 1
                      ? darkMode
                        ? "bg-gray-700/50 text-gray-500 cursor-not-allowed"
                        : "bg-slate-200 text-slate-400 cursor-not-allowed"
                      : darkMode
                      ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 hover:shadow-lg"
                      : "bg-gradient-to-r from-cyan-500 to-teal-500 text-white hover:from-cyan-600 hover:to-teal-600 hover:shadow-lg"
                  }`}
                >
                  <span>Next</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
