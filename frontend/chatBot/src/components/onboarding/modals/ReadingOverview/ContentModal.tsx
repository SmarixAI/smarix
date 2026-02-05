"use client";

import {
  X,
  BookOpen,
  FileText,
  Clock,
  ChevronLeft,
  ChevronRight,
  Loader2,
  ClipboardCheck,
  AlertCircle,
} from "lucide-react";
import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { ContentParser } from "../../utils/ReadingOverview/contentParser";
import { MermaidRenderer } from "../../utils/ReadingOverview/mermaidRenderer";
import ContentRenderer from "./ContentRenderer";
import QnATest from "./QnATest";
import { ContentService } from "../../services/ReadingOverview/contentService";
import { Inter, JetBrains_Mono } from "next/font/google";

// ─── Types ────────────────────────────────────────────────────────────────────

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
  items: any[];
}

// ─── Fonts ────────────────────────────────────────────────────────────────────

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

// ─── Component ────────────────────────────────────────────────────────────────

export default function OverviewModal({
  isOpen,
  onClose,
  title,
  moduleId,
  activeRepos = [],
  employeeId,
  onProgressUpdate,
}: ContentModalProps) {
  // ── State ───────────────────────────────────────────────────────────────────
  const [renderedMermaid, setRenderedMermaid] = useState<{
    [key: string]: { [key: number]: string };
  }>({});
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(
    new Set(),
  );
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [sections, setSections] = useState<SectionWithItems[]>([]);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [missingRepo, setMissingRepo] = useState(false);

  // ── Derived ─────────────────────────────────────────────────────────────────
  const activeSection = sections[currentSectionIndex];
  const activeItem = activeSection?.items?.[currentItemIndex];

  // ── Refs ────────────────────────────────────────────────────────────────────
  const scrollTimeoutRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const activeReposRef = useRef<string[]>([]);

  // ── Escape key handler ──────────────────────────────────────────────────────
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen, onClose]);

  // ── Track reading progress on open ──────────────────────────────────────────
  useEffect(() => {
    const repo = activeRepos && activeRepos.length > 0 ? activeRepos[0] : null;
    if (isOpen && employeeId && moduleId && repo) {
      fetch("/api/onboarding/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employeeId,
          section: "reading",
          itemId: moduleId,
          updates: { status: "in-progress", progress: 0 },
          repo,
        }),
      }).catch((err) => console.error("Error tracking reading progress:", err));
    }
  }, [isOpen, employeeId, moduleId, activeRepos]);

  // ── Fetch module content ────────────────────────────────────────────────────
  useEffect(() => {
    if (isOpen && moduleId) {
      setIsLoading(true);
      setMissingRepo(false);
      MermaidRenderer.initialize(false);

      const fetchModuleContent = async () => {
        try {
          setIsLoading(true);
          const repo =
            activeRepos && activeRepos.length > 0 ? activeRepos[0] : "";
          activeReposRef.current = activeRepos;

          if (!repo) {
            console.warn(
              "OverviewModal: No active repository assigned to user.",
            );
            setMissingRepo(true);
            setIsLoading(false);
            return;
          }

          const response = await ContentService.fetchModuleContent(
            moduleId,
            repo,
          );
          console.log("RAW BACKEND RESPONSE:", response);

          if (!response || !Array.isArray(response.sections)) {
            setIsLoading(false);
            return;
          }

          const parsed = response.sections.map((section: any) => ({
            sectionId: section.sectionId || `section-${Math.random().toString(36).slice(2)}`,
            sectionTitle: section.sectionTitle || 'Untitled Section',
            items: Array.isArray(section.items) ? section.items : [], 
          }));


          setSections(parsed);
          setCurrentSectionIndex(0);
          setCurrentItemIndex(0);
          setIsLoading(false);

          if (employeeId && moduleId && parsed.length > 0) {
            fetch("/api/onboarding/progress", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                employeeId,
                section: "reading",
                itemId: moduleId,
                updates: {
                  status: "in-progress",
                  progress: Math.round((1 / parsed.length) * 100),
                },
                repo,
              }),
            }).catch((err) =>
              console.error("Error tracking initial reading progress:", err),
            );
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
      setMissingRepo(false);
    }

    return () => {
      if (scrollTimeoutRef.current) cancelAnimationFrame(scrollTimeoutRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isOpen, moduleId, activeRepos]);

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => {
      const target = e.target as HTMLDivElement;
      const scrollHeight = target.scrollHeight - target.clientHeight;
      const progress =
        scrollHeight > 0 ? (target.scrollTop / scrollHeight) * 100 : 0;
      setScrollProgress(Math.min(100, Math.max(0, progress)));
    });
  }, []);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  // ── Flat item list for linear navigation ────────────────────────────────────
  const flatItems = useMemo(() => {
    const result: {
      sectionIndex: number;
      itemIndex: number;
      type: "teaching" | "qna";
    }[] = [];
    sections.forEach((section, sIdx) => {
      section.items.forEach((item, iIdx) => {
        result.push({
          sectionIndex: sIdx,
          itemIndex: iIdx,
          type: item.type === "qna" ? "qna" : "teaching",
        });
      });
    });
    return result;
  }, [sections]);

  const currentFlatIndex = useMemo(() => {
    return flatItems.findIndex(
      (i) =>
        i.sectionIndex === currentSectionIndex &&
        i.itemIndex === currentItemIndex,
    );
  }, [flatItems, currentSectionIndex, currentItemIndex]);

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

  // ── Memos ───────────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const totalItems = sections.reduce((sum, s) => sum + s.items.length, 0);
    return {
      estimatedReadTime: Math.ceil(totalItems * 1.5),
      totalSections: sections.length,
    };
  }, [sections]);

  const sidebarSections = useMemo(() => {
    return sections.map((section, index) => ({
      sectionId: section.sectionId,
      sectionTitle: section.sectionTitle,
      index,
    }));
  }, [sections]);

  const progressPercent = useMemo(() => {
    return sections.length > 0
      ? Math.round(((currentSectionIndex + 1) / sections.length) * 100)
      : 0;
  }, [currentSectionIndex, sections.length]);

  // ── Early exit ──────────────────────────────────────────────────────────────
  if (!isOpen) return null;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 z-[200]" onClick={handleBackdropClick}>
      {/* ─── Global Styles ─────────────────────────────────────────────────── */}
      <style jsx global>{`
        /* Animations */
        @keyframes modalIn {
          0% { opacity: 0; transform: scale(0.985); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes contentFade {
          0% { opacity: 0; transform: translateY(8px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes backdropIn {
          0% { opacity: 0; }
          100% { opacity: 1; }
        }
        .anim-modal { animation: modalIn 0.32s cubic-bezier(0.22, 1, 0.36, 1); }
        .anim-backdrop { animation: backdropIn 0.25s ease-out; }
        .anim-content { animation: contentFade 0.28s cubic-bezier(0.22, 1, 0.36, 1); }

        /* Refined scrollbar */
        .scrollbar-refined::-webkit-scrollbar { width: 6px; }
        .scrollbar-refined::-webkit-scrollbar-track { background: transparent; }
        .scrollbar-refined::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 3px;
          transition: background 0.2s;
        }
        .scrollbar-refined::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

        /* Hide scrollbar utility */
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      {/* ─── Backdrop ────────────────────────────────────────────────────── */}
      <div className="absolute inset-0 anim-backdrop bg-black/40 backdrop-blur-sm" />

      {/* ─── Shell ───────────────────────────────────────────────────────── */}
      <div
        className="relative z-10 w-screen h-screen flex flex-col bg-[#f4f6f8] anim-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Thin top progress bar */}
        <div className="absolute top-0 left-0 right-0 h-0.5 z-30 bg-transparent">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        {/* ─── Header ──────────────────────────────────────────────────── */}
        <header className="flex-shrink-0 z-20 flex items-center px-6 h-16 bg-white border-b border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          {/* Left — Breadcrumb */}
          <div className="flex items-center gap-2 w-56 flex-shrink-0">
            <span className="text-xs font-medium text-gray-400 tracking-wide uppercase">
              Onboarding
            </span>
            <span className="text-gray-300">/</span>
            <span className="text-xs font-semibold text-gray-500 tracking-wide uppercase">
              Reading
            </span>
          </div>

          {/* Center — Title + meta */}
          <div className="flex-1 flex flex-col items-center min-w-0 px-6">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md flex items-center justify-center bg-blue-50 border border-blue-100">
                <BookOpen className="w-3.5 h-3.5 text-blue-600" />
              </div>
              <h1
                className={`${inter.className} text-[15px] font-semibold text-gray-800 tracking-tight truncate max-w-lg`}
                title={title}
              >
                {title}
              </h1>
            </div>
            <div className="flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1.5 text-[11px] text-gray-400 font-medium">
                <Clock className="w-3 h-3" />
                {stats.estimatedReadTime} min read
              </span>
              <span className="text-gray-300">·</span>
              <span className="flex items-center gap-1.5 text-[11px] text-blue-500 font-semibold">
                <FileText className="w-3 h-3" />
                Section {currentSectionIndex + 1} of {sections.length}
              </span>
            </div>
          </div>

          {/* Right — Close */}
          <div className="w-56 flex justify-end flex-shrink-0">
            <button
              onClick={onClose}
              className="flex items-center justify-center w-12 h-12 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Close"
              title="Close (Esc)"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </header>

        {/* ─── Body ────────────────────────────────────────────────────── */}
        <div className="flex-1 grid grid-cols-[232px_1fr_260px] min-h-0 overflow-hidden">

          {/* ── Left Sidebar ─────────────────────────────────────────── */}
          <aside className="scrollbar-refined overflow-y-auto bg-white border-r border-gray-200 py-5 px-3">
            <p className={`${inter.className} text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-3`}>
              Sections
            </p>
            <div className="space-y-0.5">
              {sidebarSections.map(({ sectionId, sectionTitle, index }) => {
                const isActive = currentSectionIndex === index;
                return (
                  <button
                    key={sectionId}
                    onClick={() => {
                      setCurrentSectionIndex(index);
                      setCurrentItemIndex(0);
                    }}
                    className={`
                      w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150
                      ${isActive
                        ? "bg-blue-50 border border-blue-200"
                        : "border border-transparent hover:bg-gray-50"
                      }
                    `}
                  >
                    <div className="flex items-center gap-2.5">
                      {/* Index badge */}
                      <span
                        className={`
                          flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold transition-colors
                          ${isActive
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-500"
                          }
                        `}
                      >
                        {index + 1}
                      </span>
                      <span
                        className={`
                          text-[13px] font-medium truncate transition-colors
                          ${isActive ? "text-blue-700" : "text-gray-600"}
                        `}
                      >
                        {sectionTitle}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </aside>

          {/* ── Main Content ─────────────────────────────────────────── */}
          <main className="p-6 flex flex-col">
            {isLoading ? (
              /* Loading */
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="w-12 h-12 rounded-2xl bg-white border border-gray-200 shadow-sm flex items-center justify-center">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                </div>
                <p className="mt-4 text-[13px] text-gray-400 font-medium">
                  Loading content…
                </p>
              </div>
            ) : missingRepo ? (
              /* Missing repo warning */
              <div className="flex-1 flex flex-col items-center justify-center anim-content">
                <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-amber-500" />
                </div>
                <h3 className={`${inter.className} mt-4 text-[15px] font-semibold text-gray-800`}>
                  No Repository Assigned
                </h3>
                <p className="mt-1.5 text-[13px] text-gray-400 text-center max-w-[280px] leading-relaxed">
                  Contact your manager to assign an active repository to your account before continuing.
                </p>
              </div>
            ) : !activeItem ? (
              /* Empty */
              <div className="flex-1 flex items-center justify-center">
                <p className="text-[13px] text-gray-400">No content available</p>
              </div>
            ) : (
              /* Content card */
              <div className="flex-1 flex">
                <div className="flex-1 bg-white rounded-xl border border-gray-200 shadow-[0_2px_8px_rgba(0,0,0,0.04)] overflow-y-auto max-h-[80vh] scrollbar-hide anim-content">
                  <div className="p-8">
                    {/* Item title */}
                    {activeItem.title && (
                      <h2
                        className={`${inter.className} text-[20px] font-bold text-gray-900 mb-5 tracking-tight`}
                      >
                        {activeItem.title}
                      </h2>
                    )}

                    {/* Divider under title */}
                    {activeItem.title && (
                      <div className="w-10 h-0.5 bg-blue-500 rounded-full mb-6" />
                    )}

                    {/* Render Q&A or reading content */}
                    {activeItem.type === "qna" ? (
                      <QnATest
                        questions={activeItem.questions || []}
                        sectionTitle={activeSection.sectionTitle}
                        employeeId={employeeId}
                        moduleId={moduleId}
                        onProgressUpdate={onProgressUpdate}
                      />
                    ) : (
                      <ContentRenderer
                        sections={ContentParser.parseContent(
                          activeItem.content || "",
                        )}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </main>

          {/* ── Right Sidebar ────────────────────────────────────────── */}
          <aside className="scrollbar-refined overflow-y-auto bg-white border-l border-gray-200 py-5 px-4 space-y-4">

            {/* Progress card */}
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <div className="flex items-center justify-between mb-3">
                <p className={`${inter.className} text-[10px] font-bold text-gray-400 uppercase tracking-widest`}>
                  Progress
                </p>
                <span className={`${inter.className} text-[11px] font-bold text-blue-600`}>
                  {progressPercent}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full h-1.5 rounded-full bg-gray-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              {/* Section label */}
              <p className={`${inter.className} mt-2.5 text-[12px] text-gray-500`}>
                Section <span className="font-semibold text-gray-700">{currentSectionIndex + 1}</span> of{" "}
                <span className="font-semibold text-gray-700">{sections.length}</span>
              </p>
            </div>

            {/* Key Takeaways card */}
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <p className={`${inter.className} text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3`}>
                Key Takeaways
              </p>
              <ul className="space-y-2.5">
                {[
                  "Understand the problem",
                  "Identify edge cases",
                  "Incremental fixes",
                  "Maintainable logic",
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="flex-shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500" />
                    <span className={`${inter.className} text-[13px] text-gray-600`}>
                      {item}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Reading stats card */}
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <p className={`${inter.className} text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3`}>
                Reading Stats
              </p>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`${inter.className} text-[12px] text-gray-500`}>Est. time</span>
                  <span className={`${inter.className} text-[12px] font-semibold text-gray-700`}>
                    {stats.estimatedReadTime} min
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`${inter.className} text-[12px] text-gray-500`}>Sections</span>
                  <span className={`${inter.className} text-[12px] font-semibold text-gray-700`}>
                    {stats.totalSections}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`${inter.className} text-[12px] text-gray-500`}>Items</span>
                  <span className={`${inter.className} text-[12px] font-semibold text-gray-700`}>
                    {flatItems.length}
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* ─── Footer Nav ──────────────────────────────────────────────── */}
        {/* ─── Footer Nav ──────────────────────────────────────────────── */}
<footer className="flex-shrink-0 z-20 px-6 h-16 border-t border-gray-200 bg-white shadow-[0_-1px_3px_rgba(0,0,0,0.04)] flex items-center">
  
  {/* Inner Container: Controls the width and centering */}
  <div className="flex items-center justify-between w-full max-w-4xl mx-auto">
    
    {/* Previous button */}
    <button
      onClick={handlePreviousSection}
      disabled={currentFlatIndex <= 0}
      className={`
        ${inter.className}
        flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold transition-all
        ${currentFlatIndex <= 0
          ? "text-gray-300 cursor-not-allowed"
          : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"
        }
      `}
    >
      <ChevronLeft className="w-4 h-4" />
      Previous
    </button>

    {/* Dot indicators (Middle) */}
    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide px-4">
      {flatItems.map((item, idx) => {
        const isActive = idx === currentFlatIndex;
        const isPast = idx < currentFlatIndex;
        return (
          <button
            key={idx}
            onClick={() => {
              setCurrentSectionIndex(item.sectionIndex);
              setCurrentItemIndex(item.itemIndex);
            }}
            className="flex-shrink-0 flex items-center justify-center transition-all"
            aria-label={`Go to item ${idx + 1}`}
          >
            {item.type === "qna" ? (
              <ClipboardCheck
                className={`w-4 h-4 transition-colors ${
                  isActive ? "text-indigo-600" : isPast ? "text-blue-400" : "text-gray-300"
                }`}
              />
            ) : (
              <span
                className={`
                  rounded-full transition-all duration-300
                  ${isActive
                    ? "w-6 h-2 bg-gradient-to-r from-blue-500 to-indigo-500"
                    : isPast
                      ? "w-2 h-2 bg-blue-400"
                      : "w-2 h-2 bg-gray-300"
                  }
                `}
              />
            )}
          </button>
        );
      })}
    </div>

    {/* Next button */}
    <button
      onClick={handleNextSection}
      disabled={currentFlatIndex >= flatItems.length - 1}
      className={`
        ${inter.className}
        flex items-center gap-2 px-5 py-2 rounded-lg text-[13px] font-semibold transition-all
        ${currentFlatIndex >= flatItems.length - 1
          ? "bg-gray-100 text-gray-300 cursor-not-allowed"
          : "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:from-[#0E1B2E] hover:to-blue-800 shadow-lg shadow-slate-300/40"
        }
      `}
    >
      Next
      <ChevronRight className="w-4 h-4" />
    </button>
  </div>
</footer>
      </div>
    </div>
  );
}