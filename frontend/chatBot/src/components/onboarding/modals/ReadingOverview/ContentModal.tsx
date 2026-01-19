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
import QnATest from "./QnATest";
import { ContentService } from "../../services/ReadingOverview/contentService";
import type { ModuleContent } from "../../../../../types/onboarding";
import { Inter, JetBrains_Mono } from 'next/font/google';

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  moduleId: string;
  activeRepos?: string[];
  employeeId?: string | null;
  onProgressUpdate?: () => void;
}

interface ModuleWithContent {
  moduleId: string;
  moduleTitle: string;
  jsonFile: string;
  content: ModuleContent | null;
  sections: any[];
  isQnASection?: boolean;
}

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

export default function OverviewModal({
  isOpen,
  onClose,
  title,
  moduleId,
  activeRepos = [],
  employeeId,
  onProgressUpdate,
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

  // Track reading section progress when modal opens
  useEffect(() => {
    if (isOpen && employeeId && moduleId) {
      // Mark reading module as in-progress when opened
      const trackReadingProgress = async () => {
        try {
          await fetch('/api/onboarding/progress', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              employeeId,
              section: 'reading',
              itemId: moduleId,
              updates: {
                status: 'in-progress',
                progress: 0,
              },
            }),
          });
        } catch (error) {
          console.error('Error tracking reading progress:', error);
        }
      };
      trackReadingProgress();
    }
  }, [isOpen, employeeId, moduleId]);

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
                  ? []
                  : section.content?.content
                  ? ContentParser.parseContent(section.content.content)
                  : [],
                isQnASection: isQnA,
              });
            });
          }

          setModuleContent(content);
          setCurrentSectionIndex(0);
          setIsLoading(false);
          
          // Track initial progress when content is loaded
          if (employeeId && moduleId && content.length > 0) {
            fetch('/api/onboarding/progress', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                employeeId,
                section: 'reading',
                itemId: moduleId,
                updates: {
                  status: 'in-progress',
                  progress: Math.round((1 / content.length) * 100),
                },
              }),
            }).catch((error) => {
              console.error('Error tracking initial reading progress:', error);
            });
          }
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
      const renderAllMermaid = async () => {
        const mermaidByModule: { [key: string]: { [key: number]: string } } = {};

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

        setRenderedMermaid(mermaidByModule);
      };

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
      const nextIndex = prev < moduleContent.length - 1 ? prev + 1 : prev;
      
      // Track progress when moving to next section
      if (employeeId && moduleId && nextIndex > prev) {
        const progress = Math.round(((nextIndex + 1) / moduleContent.length) * 100);
        const isLastSection = nextIndex === moduleContent.length - 1;
        
        fetch('/api/onboarding/progress', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            employeeId,
            section: 'reading',
            itemId: moduleId,
            updates: {
              status: isLastSection ? 'completed' : 'in-progress',
              progress: isLastSection ? 100 : progress,
              ...(isLastSection ? { completedAt: new Date().toISOString() } : {}),
            },
          }),
        }).catch((error) => {
          console.error('Error updating reading progress:', error);
        });
      }
      
      return nextIndex;
    });
  }, [moduleContent.length, employeeId, moduleId]);

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
      className="fixed inset-0 z-[200] flex items-center justify-center p-6"
      onClick={handleBackdropClick}
    >
      <style jsx global>{`
        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: scale(0.96) translateY(20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }

        @keyframes backdropFade {
          from { opacity: 0; }
          to { opacity: 1; }
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
          animation: modalSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(14, 27, 46, 0.03);
          border-radius: 10px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, rgba(14, 27, 46, 0.15), rgba(59, 130, 246, 0.15));
          border-radius: 10px;
          border: 2px solid transparent;
          background-clip: padding-box;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, rgba(14, 27, 46, 0.25), rgba(59, 130, 246, 0.25));
          background-clip: padding-box;
        }
      `}</style>

      <div
        className="absolute inset-0 modal-backdrop bg-gradient-to-br from-[#0E1B2E]/70 via-[#0E1B2E]/60 to-blue-900/60 backdrop-blur-md"
        onClick={handleBackdropClick}
      />

      <div
        className="relative w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden modal-content bg-white/95 backdrop-blur-xl rounded-3xl border border-slate-200/60 shadow-2xl shadow-slate-900/20"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-1 z-20 bg-slate-200/50 rounded-t-3xl overflow-hidden">
          <div
            className="h-full transition-all duration-300 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-600"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        <div className="flex-shrink-0 px-8 py-5 border-b bg-white/60 backdrop-blur-xl border-slate-200/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200/50 shadow-sm">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>

              <div className="flex items-center space-x-4">
                <h2 className={`${inter.className} text-xl font-semibold text-[#0E1B2E] tracking-tight`}>
                  {title}
                </h2>

                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-50/80 backdrop-blur-sm border border-slate-200/60">
                    <Clock className="w-4 h-4 text-slate-600" />
                    <span className={`${jetbrainsMono.className} text-xs font-medium text-slate-700`}>
                      {stats.estimatedReadTime} min read
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-blue-50/80 backdrop-blur-sm border border-blue-200/60">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span className={`${jetbrainsMono.className} text-xs font-medium text-blue-700`}>
                      Section {currentSectionIndex + 1} of {moduleContent.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="flex items-center justify-center w-10 h-10 rounded-xl transition-all bg-white/80 backdrop-blur-sm border border-red-200 hover:bg-red-500 hover:border-red-500 group shadow-sm hover:shadow-md"
                aria-label="Close modal"
                title="Close (Esc)"
              >
                <X className="w-5 h-5 transition-colors text-red-600 group-hover:text-white" />
              </button>
            </div>
          </div>
        </div>

        <div
          className="flex-1 overflow-y-auto custom-scrollbar relative"
          onScroll={handleScroll}
        >
          <div className="p-8">
            {isLoading && moduleContent.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32">
                <div className="relative">
                  <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full" />
                  <Loader2 className="w-16 h-16 animate-spin text-blue-600 relative" />
                </div>
                <p className={`${inter.className} mt-6 text-sm font-medium text-slate-600`}>
                  Loading module content...
                </p>
              </div>
            ) : moduleContent.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
                  <FileText className="w-8 h-8 text-slate-400" />
                </div>
                <p className={`${inter.className} text-lg font-medium text-slate-600`}>
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
                      className="rounded-2xl overflow-hidden transition-all animate-fade-in bg-white/60 backdrop-blur-xl border border-slate-200/60 shadow-lg shadow-slate-200/30"
                    >
                      <div className="px-6 py-4 border-b border-slate-200/60 bg-gradient-to-r from-slate-50/80 to-blue-50/40 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className={`${jetbrainsMono.className} text-sm font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg`}>
                              {currentSectionIndex + 1}
                            </span>
                            <h3 className={`${inter.className} text-base font-semibold text-[#0E1B2E]`}>
                              {moduleData.moduleTitle}
                            </h3>
                          </div>

                          {moduleData.content?.quality && (
                            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200">
                              <Award className="w-4 h-4 text-amber-600" />
                              <span className={`${jetbrainsMono.className} text-xs font-semibold text-amber-700`}>
                                {(moduleData.content.quality * 5).toFixed(1)}
                              </span>
                            </div>
                          )}
                        </div>

                        {moduleData.content?.topic && !moduleData.isQnASection && (
                          <div className="mt-3">
                            <button
                              onClick={() => toggleModuleExpanded(moduleData.moduleId)}
                              className={`${inter.className} w-full text-left text-xs text-slate-600 hover:text-[#0E1B2E] transition-colors flex items-center space-x-2`}
                            >
                              <ChevronDown
                                className={`w-4 h-4 transition-transform ${
                                  expandedModules.has(moduleData.moduleId) ? "rotate-180" : ""
                                }`}
                              />
                              <span className="font-medium">Learning Objective</span>
                            </button>

                            {expandedModules.has(moduleData.moduleId) && (
                              <p className={`${inter.className} mt-2 text-sm leading-relaxed text-slate-700 pl-6`}>
                                {moduleData.content.topic}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="px-6 py-6">
                        {moduleData.isQnASection ? (
                          // Use QnATest component for ALL QnA sections
                          moduleData.content?.questions && Array.isArray(moduleData.content.questions) ? (
                            <QnATest
                              questions={moduleData.content.questions}
                              sectionTitle={moduleData.moduleTitle}
                              employeeId={employeeId}
                              moduleId={moduleId}
                              onProgressUpdate={onProgressUpdate}
                            />
                          ) : moduleData.content?.question ? (
                            // Handle single question format
                            <QnATest
                              questions={[{
                                question: moduleData.content.question,
                                options: moduleData.content.options || {},
                                correct_answer: moduleData.content.correct_answer || '',
                                explanation: moduleData.content.explanation || '',
                              }]}
                              sectionTitle={moduleData.moduleTitle}
                              employeeId={employeeId}
                              moduleId={moduleId}
                              onProgressUpdate={onProgressUpdate}
                            />
                          ) : (
                            <div className="text-center py-8 text-slate-500">
                              No questions available for this test.
                            </div>
                          )
                        ) : (
                          // Regular content display for non-QnA sections
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

        <div className="flex-shrink-0 px-8 py-5 border-t border-slate-200/60 bg-white/60 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <button
              onClick={handlePreviousSection}
              disabled={currentSectionIndex === 0}
              className={`${inter.className} flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                currentSectionIndex === 0
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg hover:scale-105"
              }`}
            >
              <ChevronLeft className="w-5 h-5" />
              <span>Previous</span>
            </button>

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
                        ? `p-2 rounded-xl border ${
                            isActive
                              ? "bg-gradient-to-br from-blue-500 to-indigo-500 border-blue-400 shadow-md"
                              : "bg-white border-slate-300 hover:bg-slate-50 hover:border-slate-400"
                          }`
                        : `h-2 rounded-full ${
                            isActive
                              ? "bg-gradient-to-r from-blue-500 to-indigo-500 w-10 shadow-md"
                              : "bg-slate-300 hover:bg-slate-400 w-2"
                          }`
                    }`}
                    aria-label={`Go to section ${index + 1}${isQnA ? " (QnA)" : ""}`}
                    title={isQnA ? "QnA Section" : `Section ${index + 1}`}
                  >
                    {isQnA ? (
                      <ClipboardCheck className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-600"}`} />
                    ) : null}
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleNextSection}
              disabled={currentSectionIndex === moduleContent.length - 1}
              className={`${inter.className} flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                currentSectionIndex === moduleContent.length - 1
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg hover:scale-105"
              }`}
            >
              <span>Next</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}