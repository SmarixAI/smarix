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
import { Inter, JetBrains_Mono } from 'next/font/google';

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  moduleId: string;
  activeRepos?: string[];
  employeeId?: string | null;
  onProgressUpdate?: (section: string, itemId: string, updates: any) => void;
}

interface SectionWithItems {
  sectionId: string;
  sectionTitle: string;
  items: any[];          // 👈 teaching + qna items
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
  const [renderedMermaid, setRenderedMermaid] = useState<{
    [key: string]: { [key: number]: string };
  }>({});
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [sections, setSections] = useState<SectionWithItems[]>([]);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const activeSection = sections[currentSectionIndex];
  const activeItem = activeSection?.items?.[currentItemIndex];

  
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
      

      const fetchModuleContent = async () => {
      try {
        setIsLoading(true);

        const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
        activeReposRef.current = activeRepos;

        const response = await ContentService.fetchModuleContent(moduleId, repo);

        console.log("RAW BACKEND RESPONSE:", response);
        console.log("SECTIONS FROM BACKEND:", response?.sections);

        if (!response || !Array.isArray(response.sections)) {
          setIsLoading(false);
          return;
        }

        /**
         * IMPORTANT:
         * We now keep SECTION → ITEMS structure intact
         * NO flattening
         */
        const sections = response.sections.map((section) => ({
          sectionId: section.sectionId,
          sectionTitle: section.sectionTitle,
          items: Array.isArray(section.items) ? section.items : [],
        }));

        setSections(sections);          // ✅ sections only (sidebar)
        setCurrentSectionIndex(0);      // ✅ first section
        setCurrentItemIndex(0);         // ✅ first item of section
        setIsLoading(false);

        // Track initial progress (section-based)
        if (employeeId && moduleId && sections.length > 0) {
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
                progress: Math.round((1 / sections.length) * 100),
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
      setRenderedMermaid({});
      setScrollProgress(0);
      setCurrentSectionIndex(0);
    }

    return () => {
      
      if (scrollTimeoutRef.current) {
        cancelAnimationFrame(scrollTimeoutRef.current);
      }
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isOpen, moduleId, activeRepos]);



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

  const flatItems = useMemo(() => {
    const result: {
      sectionIndex: number;
      itemIndex: number;
      type: 'teaching' | 'qna';
    }[] = [];

    sections.forEach((section, sIdx) => {
      section.items.forEach((item, iIdx) => {
        result.push({
          sectionIndex: sIdx,
          itemIndex: iIdx,
          type: item.type === 'qna' ? 'qna' : 'teaching',
        });
      });
    });

    return result;
  }, [sections]);

  const currentFlatIndex = useMemo(() => {
    return flatItems.findIndex(
      i =>
        i.sectionIndex === currentSectionIndex &&
        i.itemIndex === currentItemIndex
    );
  }, [flatItems, currentSectionIndex, currentItemIndex]);



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




  const handleNextSection = () => {
    if (currentFlatIndex < flatItems.length - 1) {
      const next = flatItems[currentFlatIndex + 1];
      setCurrentSectionIndex(next.sectionIndex);
      setCurrentItemIndex(next.itemIndex);
    }
  };

  const handlePreviousSection = () => {
    if (currentFlatIndex > 0) {
      const prev = flatItems[currentFlatIndex - 1];
      setCurrentSectionIndex(prev.sectionIndex);
      setCurrentItemIndex(prev.itemIndex);
    }
  };



  const handleBackdropClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  const stats = useMemo(() => {
    const totalItems = sections.reduce((sum, s) => sum + s.items.length, 0);
    const estimatedReadTime = Math.ceil(totalItems * 1.5); // heuristic
    return { estimatedReadTime, totalSections: sections.length };
  }, [sections]);


  const sidebarSections = useMemo(() => {
    return sections.map((section, index) => ({
      sectionId: section.sectionId,
      sectionTitle: section.sectionTitle,
      index,
    }));
  }, [sections]);



  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[200]"
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
        className="absolute inset-0 modal-backdrop bg-gradient-to-br from-[#0E1B2E]/70 via-[#0E1B2E]/60 to-blue-900/60 pointer-events-none"
      />


      <div
        className="relative z-10 w-screen h-screen flex flex-col overflow-hidden bg-white pointer-events-auto"
        onClick={(e) => e.stopPropagation()}
      >

        <div className="absolute top-0 left-0 right-0 h-1 z-20 bg-slate-200/50 rounded-t-3xl overflow-hidden">
          <div
            className="h-full transition-all duration-300 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-600"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        {/* TOP HEADER */}
        <div className="sticky bottom-0 z-20 flex-shrink-0 px-8 py-5 border-t bg-white/60 backdrop-blur-xl">
          <div className="grid grid-cols-[260px_1fr_320px] items-center">

            {/* LEFT HEADER — Reading / Overview */}
            <div className="px-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Employee
                </span>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Onboarding
                </span>
              </div>

              <h1
                className={`${inter.className} mt-1 text-xl font-bold text-[#0E1B2E] tracking-tight`}
              >
                Reading Overview
              </h1>
            </div>

            {/* CENTER HEADER — Module Title + Meta */}
            <div className="flex items-center gap-4 px-4 min-w-0">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-50 border border-blue-200/50 flex-shrink-0">
                <BookOpen className="w-5 h-5 text-blue-600" />
              </div>

              <div className="min-w-0">
                <h2
                  className={`${inter.className} text-lg font-semibold text-[#0E1B2E] tracking-tight truncate`}
                  title={title}
                >
                  {title}
                </h2>

                <div className="flex items-center gap-3 mt-1">
                  <div className="flex items-center gap-1 text-xs text-slate-600">
                    <Clock className="w-3.5 h-3.5" />
                    {stats.estimatedReadTime} min read
                  </div>

                  <div className="flex items-center gap-1 text-xs text-blue-600">
                    <FileText className="w-3.5 h-3.5" />
                    Section {currentSectionIndex + 1} of {sections.length}
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT HEADER — Back / Close */}
            <div className="flex items-center justify-end gap-3 pr-2">
              {/* Close (optional but recommended) */}
              <button
                onClick={onClose}
                className="flex items-center justify-center w-10 h-10 rounded-xl bg-white border border-red-200 hover:bg-red-500 hover:border-red-500 group transition-all shadow-sm"
                aria-label="Close"
                title="Close (Esc)"
              >
                <X className="w-5 h-5 text-red-600 group-hover:text-white" />
              </button>
            </div>

          </div>
        </div>



        <div className="flex-1 grid grid-cols-[260px_1fr_320px] min-h-0">

          {/* LEFT SIDEBAR */}
          <aside className="h-full overflow-y-auto border-r border-slate-200 bg-white/70 backdrop-blur-xl p-4">
            <h3 className={`${inter.className} text-xs font-bold text-slate-500 mb-4`}>
              Sections
            </h3>

            <div className="space-y-2">
              {sidebarSections.map(({ sectionId, sectionTitle, index }, i) => {
                const isActive = currentSectionIndex === index;
                return (
                  <button
                    key={sectionId}
                    onClick={() => {
                      setCurrentSectionIndex(index);
                      setCurrentItemIndex(0);
                    }}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all ${
                      isActive
                        ? "bg-blue-600 text-white shadow"
                        : "hover:bg-slate-100 text-slate-700"
                    }`}
                  >
                    <div className="text-[11px] font-semibold opacity-70">
                      Section {i + 1}
                    </div>

                    <div className="text-sm font-medium truncate">
                      {sectionTitle}
                    </div>
                  </button>
                );
              })}
            </div>


          </aside>

          {/* CENTER CONTENT */}
          <main className="min-h-0 overflow-y-auto custom-scrollbar p-4">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-32">
                <Loader2 className="w-16 h-16 animate-spin text-blue-600" />
                <p className="mt-6 text-sm text-slate-600">Loading module content...</p>
              </div>
            ) : !activeItem ? (
              <div className="text-center py-32 text-slate-500">
                No content available
              </div>
            ) : (
              <div className="rounded-2xl bg-white/60 border shadow-lg p-6 animate-fade-in">
              
                {/* 🔹 ITEM TITLE (NEW) */}
                {activeItem.title && (
                  <h4 className="mb-4 text-xl font-semibold text-slate-900">
                    {activeItem.title}
                  </h4>
                )}

                {/* CONTENT */}
                {activeItem.type === 'qna' ? (
                  <QnATest
                    questions={activeItem.questions || []}
                    sectionTitle={activeSection.sectionTitle}
                    employeeId={employeeId}
                    moduleId={moduleId}
                    onProgressUpdate={onProgressUpdate}
                  />
                ) : (
                  <ContentRenderer
                    sections={ContentParser.parseContent(activeItem.content || '')}
                    renderedMermaid={renderedMermaid[activeSection.sectionId] || {}}
                  />
                )}
              </div>
            )}
          </main>


          {/* RIGHT SIDEBAR */}
          <aside className="h-full overflow-y-auto p-4 space-y-6 border-l border-slate-200 bg-gradient-to-b from-white/80 to-blue-50/40 backdrop-blur-xl">
            {/* Progress */}
            <div className="rounded-2xl p-4 bg-white shadow-sm border">
              <p className="text-xs font-semibold text-slate-500 mb-2">
                Progress
              </p>

              <p className="text-sm font-bold text-[#0E1B2E] mb-1">
                Section 2 of 6
              </p>

              <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden mt-2">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-500"
                  style={{ width: "35%" }}
                />
              </div>

              <p className="mt-2 text-xs text-slate-500">
                35% completed
              </p>
            </div>
            {/* Key Takeaways */}
            <div className="rounded-2xl p-4 bg-white shadow-sm border">
              <h4 className="text-sm font-bold mb-3">
                Key Takeaways
              </h4>

              <ul className="space-y-2 text-sm text-slate-700">
                {[
                  "Understand the problem before touching the code",
                  "Identify edge cases early",
                  "Prefer small, incremental fixes",
                  "Write readable and maintainable logic",
                ].map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="w-1.5 h-1.5 mt-2 bg-blue-500 rounded-full flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div className="rounded-2xl p-4 bg-white shadow-sm border">
              <h4 className="text-sm font-bold mb-3">
                Resources
              </h4>

              <div className="space-y-2 text-sm">
                {[
                  { label: "Official Documentation", hint: "API & reference" },
                  { label: "Code Style Guide", hint: "Best practices" },
                  { label: "Common Pitfalls", hint: "Avoid mistakes" },
                  { label: "Related Challenges", hint: "Practice more" },
                ].map((res, i) => (
                  <div
                    key={i}
                    className="px-3 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 cursor-pointer transition-colors"
                  >
                    <p className="font-medium text-slate-800">
                      {res.label}
                    </p>
                    <p className="text-xs text-slate-500">
                      {res.hint}
                    </p>
                  </div>
                ))}
              </div>
            </div>

          </aside>
        </div>

        <div className="flex-shrink-0 px-8 py-5 border-t border-slate-200/60 bg-white/60 backdrop-blur-xl">
          <div className="flex items-center justify-center gap-10">

            {/* Previous */}
            <button
              onClick={handlePreviousSection}
              disabled={currentFlatIndex <= 0}
              className={`${inter.className} flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                currentFlatIndex <= 0
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg hover:scale-105"
              }`}
            >
              <ChevronLeft className="w-5 h-5" />
              <span>Previous</span>
            </button>


            {/* Indicators */}
            <div className="flex items-center space-x-2">
              {flatItems.map((item, idx) => {
                const isActive = idx === currentFlatIndex;

                return (
                  <button
                    key={idx}
                    onClick={() => {
                      setCurrentSectionIndex(item.sectionIndex);
                      setCurrentItemIndex(item.itemIndex);
                    }}
                    className={`flex items-center justify-center transition-all ${
                      isActive
                        ? "scale-110"
                        : "opacity-60 hover:opacity-100"
                    }`}
                  >
                    {item.type === 'qna' ? (
                      <ClipboardCheck
                        className={`w-4 h-4 ${
                          isActive ? "text-indigo-600" : "text-slate-400"
                        }`}
                      />
                    ) : (
                      <span
                        className={`h-2 rounded-full transition-all ${
                          isActive
                            ? "bg-gradient-to-r from-blue-500 to-indigo-500 w-10"
                            : "bg-slate-300 w-2"
                        }`}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Next */}
            <button
              onClick={handleNextSection}
              disabled={
                currentFlatIndex >= flatItems.length - 1
              }
              className={`${inter.className} flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                currentFlatIndex >= flatItems.length - 1
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