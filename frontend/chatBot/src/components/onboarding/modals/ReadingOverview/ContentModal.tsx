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
  ArrowLeft,
  ClipboardCheck,
} from "lucide-react";
import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { ContentParser } from "../../utils/ReadingOverview/contentParser";
import { MermaidRenderer } from "../../utils/ReadingOverview/mermaidRenderer";
import ContentRenderer from "./ContentRenderer";
import { ContentService } from "../../services/ReadingOverview/contentService";
import type { ModuleContent } from "../../../../../types/onboarding";

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
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
}

export default function OverviewModal({
  isOpen,
  onClose,
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
  
  const scrollTimeoutRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const activeReposRef = useRef<string[]>([]);

  // Handle Escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen && moduleId) {
      setIsLoading(true);
      MermaidRenderer.initialize(false);
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
              const isQnA = section.content?.type === 'qna';
              const isTeaching = section.content?.type === 'teaching_content';
              
              content.push({
                moduleId: section.sectionId,
                moduleTitle: section.sectionTitle,
                jsonFile: response.jsonFile,
                content: section.content,
                sections: isTeaching && section.content?.content
                  ? ContentParser.parseContent(section.content.content)
                  : isQnA
                  ? [] // QnA sections will be rendered separately
                  : section.content?.content
                  ? ContentParser.parseContent(section.content.content)
                  : [],
                isQnASection: isQnA,
              });
            });
          }

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
  }, [isOpen, moduleId, activeRepos]);

  useEffect(() => {
    if (isOpen && moduleContent.length > 0) {
      // Render mermaid diagrams asynchronously without blocking UI
      const renderAllMermaid = async () => {
        const mermaidByModule: { [key: string]: { [key: number]: string } } = {};

        // Process mermaid rendering in batches to avoid blocking
        for (const moduleData of moduleContent) {
          if (moduleData.content?.content) {
            const mermaidDiagrams = ContentParser.extractMermaidDiagrams(
              moduleData.content.content
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





  const handleBackdropClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  const stats = useMemo(() => {
    const totalWords = moduleContent.reduce(
      (sum, mod) => sum + (mod.content?.content?.length || 0),
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
          animation: modalSlideUp 0.3s ease-out;
        }

        .custom-scrollbar {
          will-change: scroll-position;
          transform: translateZ(0);
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 10px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 10px;
          margin: 8px 0;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
          border: 2px solid #f1f5f9;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>

      <div
        className="absolute inset-0 modal-backdrop bg-[#0E1B2E]/60 backdrop-blur-sm"
        onClick={handleBackdropClick}
      />

      <div
        className="relative w-full h-full flex flex-col modal-content bg-white"
        style={{
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Progress Bar */}
        <div className="absolute top-0 left-0 right-0 h-1 z-20 bg-[#0E1B2E]/10">
          <div
            className="h-full transition-all duration-300 bg-[#0E1B2E]"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        {/* Top Navigation - Fixed */}
        <div
          className="flex-shrink-0 px-6 py-4 border-b bg-white/35 backdrop-blur-xl border-[#0E1B2E]/10 shadow-sm z-10"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                <BookOpen className="w-5 h-5 text-[#0E1B2E]" />
              </div>

              <div className="flex items-center space-x-4">
                <h2 className="text-xl font-semibold text-[#0E1B2E] tracking-tight">
                  {title}
                </h2>

                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                    <Clock className="w-4 h-4 text-[#0E1B2E]/60" />
                    <span className="text-xs font-medium text-[#0E1B2E]">
                      {stats.estimatedReadTime} min read
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                    <FileText className="w-4 h-4 text-[#0E1B2E]/60" />
                    <span className="text-xs font-medium text-[#0E1B2E]">
                      Section {currentSectionIndex + 1} of {moduleContent.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all bg-white border-2 border-[#0E1B2E]/20 hover:bg-[#0E1B2E] hover:border-[#0E1B2E] hover:text-white group shadow-sm"
                aria-label="Go back"
              >
                <ArrowLeft className="w-5 h-5 transition-colors text-[#0E1B2E] group-hover:text-white" />
                <span className="text-sm font-semibold text-[#0E1B2E] group-hover:text-white">Back</span>
              </button>
              <button
                onClick={onClose}
                className="flex items-center justify-center w-10 h-10 rounded-lg transition-all bg-white border-2 border-red-200 hover:bg-red-500 hover:border-red-500 group shadow-sm"
                aria-label="Close modal"
                title="Close (Esc)"
              >
                <X className="w-5 h-5 transition-colors text-red-600 group-hover:text-white" />
              </button>
            </div>
          </div>
        </div>

        {/* Scrollable Content Box - Fixed height */}
        <div
          className="flex-1 overflow-y-auto custom-scrollbar relative"
          onScroll={handleScroll}
        >
          {/* Floating Close Button - Top Right */}
          <div className="sticky top-4 z-30 flex justify-end pr-6 pt-4 -mb-4">
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all bg-white/90 backdrop-blur-sm border-2 border-red-200 hover:bg-red-500 hover:border-red-500 group shadow-lg"
              aria-label="Close modal"
              title="Close (Esc)"
            >
              <X className="w-4 h-4 transition-colors text-red-600 group-hover:text-white" />
              <span className="text-sm font-semibold text-red-600 group-hover:text-white">Close</span>
            </button>
          </div>

          <div className="w-full px-6 pt-6 pb-4">
            {isLoading && moduleContent.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32">
                <div className="relative">
                  <Loader2 className="w-16 h-16 animate-spin text-gray-600" />
                </div>
                <p className="mt-4 text-sm font-medium text-gray-600">
                  Loading module...
                </p>
              </div>
            ) : moduleContent.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32">
                <p className="text-lg font-medium text-gray-600">
                  No content found
                </p>
              </div>
            ) : moduleContent.length > 0 && currentSectionIndex < moduleContent.length ? (
              <div className="flex flex-col">
                {(() => {
                  const moduleData = moduleContent[currentSectionIndex];
                  return (
                    <div
                      key={moduleData.moduleId}
                      id={`module-section-${moduleData.moduleId}`}
                      className="rounded-xl overflow-hidden transition-all animate-fade-in bg-white/35 backdrop-blur-xl border border-white/25 shadow-md shadow-black/5"
                    >
                      <div
                        className="px-5 py-3 border-b border-[#0E1B2E]/10 bg-white/40 backdrop-blur-sm"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2.5">
                            <span className="text-sm font-semibold text-[#0E1B2E]/60">
                              {currentSectionIndex + 1}.
                            </span>
                            <h3 className="text-sm font-semibold text-[#0E1B2E]">
                              {moduleData.moduleTitle}
                            </h3>
                          </div>

                          {moduleData.content?.quality && (
                            <div className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-amber-50 border border-amber-200">
                              <Award className="w-3 h-3 text-amber-600" />
                              <span className="text-xs font-semibold text-amber-700">
                                {(moduleData.content.quality * 5).toFixed(1)}
                              </span>
                            </div>
                          )}
                        </div>

                        {moduleData.content?.topic && !moduleData.isQnASection && (
                          <div className="mt-2.5">
                            <button
                              onClick={() => toggleModuleExpanded(moduleData.moduleId)}
                              className="w-full text-left text-xs text-[#0E1B2E]/60 hover:text-[#0E1B2E] transition-colors flex items-center space-x-1.5"
                            >
                              <ChevronDown
                                className={`w-3.5 h-3.5 transition-transform ${
                                  expandedModules.has(moduleData.moduleId) ? "rotate-180" : ""
                                }`}
                              />
                              <span className="font-medium">Learning Objective</span>
                            </button>

                            {expandedModules.has(moduleData.moduleId) && (
                              <p className="mt-1.5 text-xs leading-relaxed text-[#0E1B2E]/70">
                                {moduleData.content.topic}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="px-5 py-4">
                        {moduleData.isQnASection ? (
                          // Render QnA section - all questions together
                          <div className="space-y-6">
                            {moduleData.content?.questions && Array.isArray(moduleData.content.questions) ? (
                              // Multiple questions (all QnA from a section)
                              moduleData.content.questions.map((qnaItem: any, qnaIndex: number) => (
                                <div key={qnaIndex} className="border-b border-[#0E1B2E]/10 pb-6 last:border-b-0 last:pb-0">
                                  <div className="mb-4">
                                    <div className="flex items-center space-x-2 mb-2">
                                      <span className="text-xs font-semibold text-[#0E1B2E]/60 bg-[#0E1B2E]/10 px-2 py-1 rounded">
                                        Question {qnaIndex + 1}
                                      </span>
                                      {qnaItem.subsection && (
                                        <span className="text-xs text-[#0E1B2E]/50 italic">
                                          {qnaItem.subsection}
                                        </span>
                                      )}
                                    </div>
                                    <h4 className="text-sm font-semibold text-[#0E1B2E] mb-3">
                                      {qnaItem.question}
                                    </h4>
                                  </div>
                                  {qnaItem.options && (
                                    <div className="mb-4">
                                      <div className="space-y-2">
                                        {Object.entries(qnaItem.options).map(([key, value]) => (
                                          <div
                                            key={key}
                                            className={`p-3 rounded-lg border ${
                                              key === qnaItem.correct_answer
                                                ? 'bg-green-50 border-green-200'
                                                : 'bg-gray-50 border-gray-200'
                                            }`}
                                          >
                                            <span className="font-semibold text-[#0E1B2E] mr-2">
                                              {key}:
                                            </span>
                                            <span className="text-sm text-[#0E1B2E]/80">
                                              {value as string}
                                            </span>
                                            {key === qnaItem.correct_answer && (
                                              <span className="ml-2 text-xs font-semibold text-green-700">
                                                ✓ Correct
                                              </span>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  {qnaItem.explanation && (
                                    <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-200">
                                      <h5 className="text-xs font-semibold text-blue-900 mb-2">
                                        Explanation:
                                      </h5>
                                      <p className="text-sm text-blue-800 leading-relaxed">
                                        {qnaItem.explanation}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              ))
                            ) : (
                              // Single question (backward compatibility)
                              <>
                                {moduleData.content?.question && (
                                  <div className="mb-4">
                                    <h4 className="text-sm font-semibold text-[#0E1B2E] mb-3">
                                      Question:
                                    </h4>
                                    <p className="text-sm text-[#0E1B2E]/80 leading-relaxed">
                                      {moduleData.content.question}
                                    </p>
                                  </div>
                                )}
                                {moduleData.content?.options && (
                                  <div className="mb-4">
                                    <h4 className="text-sm font-semibold text-[#0E1B2E] mb-3">
                                      Options:
                                    </h4>
                                    <div className="space-y-2">
                                      {Object.entries(moduleData.content.options).map(([key, value]) => (
                                        <div
                                          key={key}
                                          className={`p-3 rounded-lg border ${
                                            key === moduleData.content.correct_answer
                                              ? 'bg-green-50 border-green-200'
                                              : 'bg-gray-50 border-gray-200'
                                          }`}
                                        >
                                          <span className="font-semibold text-[#0E1B2E] mr-2">
                                            {key}:
                                          </span>
                                          <span className="text-sm text-[#0E1B2E]/80">
                                            {value as string}
                                          </span>
                                          {key === moduleData.content.correct_answer && (
                                            <span className="ml-2 text-xs font-semibold text-green-700">
                                              ✓ Correct
                                            </span>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {moduleData.content?.explanation && (
                                  <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-200">
                                    <h4 className="text-sm font-semibold text-blue-900 mb-2">
                                      Explanation:
                                    </h4>
                                    <p className="text-sm text-blue-800 leading-relaxed">
                                      {moduleData.content.explanation}
                                    </p>
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        ) : (
                          <ContentRenderer
                            sections={moduleData.sections}
                            renderedMermaid={renderedMermaid[moduleData.moduleId] || {}}
                          />
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : null}
          </div>
        </div>

        {/* Navigation Buttons - Fixed at bottom, centered */}
        <div className="flex-shrink-0 flex items-center justify-center gap-4 px-6 py-4 border-t border-[#0E1B2E]/10 bg-white z-10">
          <button
            onClick={handlePreviousSection}
            disabled={currentSectionIndex === 0}
            className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
              currentSectionIndex === 0
                ? "bg-[#0E1B2E]/10 text-[#0E1B2E]/40 cursor-not-allowed"
                : "bg-[#0E1B2E] text-white hover:bg-[#1a2f4d]"
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            <span>Previous</span>
          </button>

          {/* Progress Dots */}
          <div className="flex items-center space-x-2">
            {moduleContent.map((module, index) => {
              const isQnA = module.isQnASection;
              const isActive = index === currentSectionIndex;
              
              return (
                <button
                  key={index}
                  onClick={() => setCurrentSectionIndex(index)}
                  className={`transition-all duration-300 ${
                    isQnA
                      ? `p-1.5 rounded-lg ${
                          isActive
                            ? "bg-[#0E1B2E] text-white"
                            : "bg-[#0E1B2E]/20 text-[#0E1B2E]/60 hover:bg-[#0E1B2E]/30"
                        }`
                      : `h-2 rounded-full ${
                          isActive
                            ? "bg-[#0E1B2E] w-8"
                            : "bg-[#0E1B2E]/30 hover:bg-[#0E1B2E]/50 w-2"
                        }`
                  }`}
                  aria-label={`Go to section ${index + 1}${isQnA ? " (QnA)" : ""}`}
                  title={isQnA ? "QnA Section" : `Section ${index + 1}`}
                >
                  {isQnA ? (
                    <ClipboardCheck className="w-3.5 h-3.5" />
                  ) : null}
                </button>
              );
            })}
          </div>

          <button
            onClick={handleNextSection}
            disabled={currentSectionIndex === moduleContent.length - 1}
            className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
              currentSectionIndex === moduleContent.length - 1
                ? "bg-[#0E1B2E]/10 text-[#0E1B2E]/40 cursor-not-allowed"
                : "bg-[#0E1B2E] text-white hover:bg-[#1a2f4d]"
            }`}
          >
            <span>Next</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}