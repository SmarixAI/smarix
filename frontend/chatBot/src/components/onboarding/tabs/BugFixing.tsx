"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Code2,
  Search,
  ChevronRight,
  AlertCircle,
  FileCode2,
  Loader2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Inter } from "next/font/google";
import { useAuth } from "@/components/auth/AuthContext";

// ─── Font ───────────────────────────────────────────────────────────────────
const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

// ─── Types ──────────────────────────────────────────────────────────────────
type FilterType = "all" | "tutorials" | "challenges";

interface BugFixingProps {
  activeRepos?: string[];
  employeeId?: string | null;
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

interface BugListItem {
  id: number;
  type: "tutorial" | "challenge";
  title: string;
  description: string;
  difficulty: "Easy" | "Medium" | "Hard";
  prNumber: number;
  filesChanged: number;
  category?: string;
}

// ─── Style Maps ─────────────────────────────────────────────────────────────
const DIFFICULTY = {
  Easy:   { bg: "bg-emerald-50",   border: "border-emerald-200", text: "text-emerald-700" },
  Medium: { bg: "bg-amber-50",     border: "border-amber-200",   text: "text-amber-700"   },
  Hard:   { bg: "bg-red-50",       border: "border-red-200",     text: "text-red-700"     },
} as const;

// ─── Component ──────────────────────────────────────────────────────────────
export default function BugFixing({
  activeRepos: propActiveRepos = [],
  employeeId,
  onboardingData,
  onUpdateProgress,
}: BugFixingProps) {
  const router = useRouter();
  const { user } = useAuth();

  // Resolve repo: props → auth context → empty
  const activeRepos = propActiveRepos.length > 0 ? propActiveRepos : user?.activeRepos || [];
  const currentRepo = activeRepos[0] || "";

  // ── State ─────────────────────────────────────────────────────────────────
  const [tutorials,    setTutorials]    = useState<any>(null);
  const [challenges,   setChallenges]   = useState<any>(null);
  const [loading,      setLoading]      = useState(true);
  const [missingRepo,  setMissingRepo]  = useState(false);
  const [filter,       setFilter]       = useState<FilterType>("all");
  const [search,       setSearch]       = useState("");

  // ── Fetch ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setMissingRepo(false);

      if (!currentRepo) {
        setMissingRepo(true);
        setLoading(false);
        return;
      }

      const repoParam = `?repo=${encodeURIComponent(currentRepo)}`;
      try {
        const [tutRes, chalRes] = await Promise.all([
          fetch(`/api/onboarding/bugFix/tutorials${repoParam}`),
          fetch(`/api/onboarding/bugFix/challenges${repoParam}`),
        ]);
        if (tutRes.ok)  setTutorials(await tutRes.json());
        if (chalRes.ok) setChallenges(await chalRes.json());
      } catch (err) {
        console.error("Error fetching bug fix data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [currentRepo]);

  // ── Derived list ──────────────────────────────────────────────────────────
  const bugs: BugListItem[] = useMemo(() => {
    // — Tutorials —
    const tutorialItems = (tutorials?.tutorials || []).map((t: any) => {
      let title = t.pr_title;
      if (!title && t.raw_response) {
        const m = t.raw_response.match(/^#\s*Tutorial.*?:(.+?)$/m);
        if (m) title = m[1].trim();
      }
      let description = t.brief_description;
      if (!description && t.raw_response) {
        const m = t.raw_response.match(/##\s*1\.?\s*Overview\s*\n+([\s\S]*?)(?=\n##)/);
        if (m) description = m[1].trim().slice(0, 150) + "…";
      }
      return {
        id: t.tutorial_number,
        type: "tutorial" as const,
        title: title || `Tutorial for PR #${t.pr_number}`,
        description: description || "Learn how this PR was implemented.",
        difficulty: (t.difficulty || "Medium") as "Easy" | "Medium" | "Hard",
        prNumber: t.pr_number,
        filesChanged: t.code_files_modified || 0,
      };
    });

    // — Challenges —
    const challengeItems = (challenges?.questions || []).map((c: any) => {
      let parsed: any = {};
      try {
        parsed = typeof c.raw_response === "string" ? JSON.parse(c.raw_response) : c.raw_response;
      } catch {
        parsed = { title: "Coding Challenge", problem: c.raw_response };
      }
      return {
        id: c.question_number,
        type: "challenge" as const,
        title: parsed.title || `Challenge #${c.question_number}`,
        description: parsed.problem ? parsed.problem.slice(0, 120) + "…" : "Solve the coding problem.",
        difficulty: "Medium" as const,
        prNumber: c.question_number,
        filesChanged: 1,
        category: c.category,
      };
    });

    // — Filter + Search —
    return [...tutorialItems, ...challengeItems].filter((item) => {
      if (filter === "tutorials"  && item.type !== "tutorial")  return false;
      if (filter === "challenges" && item.type !== "challenge") return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          item.title.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.id.toString().includes(q)
        );
      }
      return true;
    });
  }, [tutorials, challenges, filter, search]);

  // ── Navigation ────────────────────────────────────────────────────────────
  const handleBugClick = (bug: BugListItem) => {
    router.push(`/employee/onboarding/bug-fix/${bug.type}/${bug.id}`);
  };

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] bg-gray-50">
        <div className="w-12 h-12 rounded-2xl bg-white border border-gray-200 shadow-sm flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        </div>
        <p className={`${inter.className} mt-4 text-[13px] text-gray-400 font-medium`}>
          Loading tasks…
        </p>
      </div>
    );
  }

  // ── Missing Repo ──────────────────────────────────────────────────────────
  if (missingRepo) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] bg-gray-50 p-12 text-center">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center">
          <AlertCircle className="w-6 h-6 text-amber-500" />
        </div>
        <h3 className={`${inter.className} mt-4 text-[15px] font-semibold text-gray-800`}>
          No Repository Assigned
        </h3>
        <p className={`${inter.className} mt-1.5 text-[13px] text-gray-400 max-w-[280px] leading-relaxed`}>
          Bug-fixing tasks are tied to your project. Ask your manager to assign an active repository.
        </p>
      </div>
    );
  }

  // ── Main ──────────────────────────────────────────────────────────────────
  return (
    <div className={`${inter.className} flex flex-col bg-gray-50 h-full`}>
      <style>{`
        @keyframes rowIn {
          0%  { opacity: 0; transform: translateY(6px); }
          100%{ opacity: 1; transform: translateY(0);   }
        }
        .row-animate { animation: rowIn 0.22s cubic-bezier(0.22,1,0.36,1) both; }
      `}</style>

      {/* ─── Header ───────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        {/* Title row */}
        <div className="px-6 pt-5 pb-2">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
              <FileCode2 className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h1 className={`text-[18px] font-bold text-gray-900 tracking-tight`}>
                Bug Fix Training
              </h1>
              <p className={`text-[13px] text-gray-400 mt-0.5`}>
                Debug real-world pull requests from your repository
              </p>
            </div>
          </div>
        </div>

        {/* Filter + Search row */}
        <div className="px-6 pb-4 flex items-center justify-between gap-4">
          {/* Pill group */}
          <div className="flex items-center bg-gray-100 rounded-lg p-0.5 gap-0.5">
            {(["all", "tutorials", "challenges"] as FilterType[]).map((f) => {
              const active = filter === f;
              const labels: Record<FilterType, string> = { all: "All", tutorials: "Tutorials", challenges: "Challenges" };
              return (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`
                    px-3.5 py-1.5 rounded-md text-[13px] font-medium transition-all duration-150
                    ${active
                      ? "bg-white text-gray-900 shadow-[0_1px_3px_rgba(0,0,0,0.12)] border border-gray-200"
                      : "text-gray-500 hover:text-gray-700 border border-transparent"
                    }
                  `}
                >
                  {labels[f]}
                </button>
              );
            })}
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search bugs, PRs…"
              className={`
                w-64 pl-8 pr-4 py-2 text-[13px] bg-white border border-gray-200 rounded-lg
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
                placeholder-gray-400 text-gray-700 transition-shadow
              `}
            />
          </div>
        </div>
      </header>

      {/* ─── Stats bar ────────────────────────────────────────────────── */}
      <div className="px-6 py-3 flex items-center gap-4">
        <span className={`text-[12px] font-semibold text-gray-500`}>
          <span className="text-gray-800">{bugs.length}</span> item{bugs.length !== 1 ? "s" : ""}
        </span>
        {/* Mini counts */}
        <div className="flex items-center gap-3 ml-auto">
          <span className="flex items-center gap-1.5 text-[11px] text-gray-400">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            {bugs.filter(b => b.type === "tutorial").length} tutorials
          </span>
          <span className="text-gray-300">·</span>
          <span className="flex items-center gap-1.5 text-[11px] text-gray-400">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            {bugs.filter(b => b.type === "challenge").length} challenges
          </span>
        </div>
      </div>

      {/* ─── List ─────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="bg-white border border-gray-200 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] overflow-hidden divide-y divide-gray-100">

          {bugs.length === 0 ? (
            /* ── Empty state ─────────────────────────────────────── */
            <div className="py-16 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center mb-3">
                <Search className="w-5 h-5 text-gray-400" />
              </div>
              <p className={`text-[14px] font-semibold text-gray-700`}>No items found</p>
              <p className={`text-[13px] text-gray-400 mt-1`}>
                Try adjusting your filters or search query
              </p>
            </div>
          ) : (
            bugs.map((bug, idx) => {
              const diff = DIFFICULTY[bug.difficulty];
              const isTutorial = bug.type === "tutorial";

              return (
                <div
                  key={`${bug.type}-${bug.id}`}
                  onClick={() => handleBugClick(bug)}
                  className="row-animate group relative flex items-start gap-4 px-5 py-4 cursor-pointer transition-colors duration-150 hover:bg-blue-50/40"
                  style={{ animationDelay: `${idx * 0.04}s` }}
                >
                  {/* Hover left-edge accent */}
                  <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500 rounded-r opacity-0 group-hover:opacity-100 transition-opacity duration-150" />

                  {/* Icon */}
                  <div
                    className={`
                      flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-colors
                      ${isTutorial
                        ? "bg-blue-50  border border-blue-200  text-blue-600  group-hover:bg-blue-100"
                        : "bg-amber-50 border border-amber-200 text-amber-600 group-hover:bg-amber-100"
                      }
                    `}
                  >
                    {isTutorial ? <BookOpen className="w-4 h-4" /> : <Code2 className="w-4 h-4" />}
                  </div>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    {/* Top row: id + title + difficulty */}
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`text-[11px] font-mono font-semibold text-gray-400`}>
                          #{bug.id}
                        </span>
                        <h3 className={`text-[14px] font-semibold text-gray-800 truncate group-hover:text-blue-700 transition-colors`}>
                          {bug.title}
                        </h3>
                      </div>

                      {/* Difficulty badge */}
                      <span className={`
                        flex-shrink-0 inline-flex items-center justify-center px-2 py-0.5 rounded-md
                        text-[11px] font-semibold border w-15
                        ${diff.bg} ${diff.border} ${diff.text}
                      `}>
                        {bug.difficulty}
                      </span>
                    </div>

                    {/* Description */}
                    <p className={`text-[13px] text-gray-500 mt-0.5 truncate`}>
                      {bug.description}
                    </p>

                    {/* Meta row: type tag + category + files */}
                    <div className="flex items-center gap-3 mt-2">
                      <span
                        className={`
                          inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border
                          ${isTutorial
                            ? "bg-blue-50  border-blue-200  text-blue-600"
                            : "bg-amber-50 border-amber-200 text-amber-600"
                          }
                        `}
                      >
                        {isTutorial ? <BookOpen className="w-2.5 h-2.5" /> : <Code2 className="w-2.5 h-2.5" />}
                        {isTutorial ? "Tutorial" : "Challenge"}
                      </span>

                      {bug.category && (
                        <>
                          <span className="text-gray-200">·</span>
                          <span className={`text-[11px] text-gray-400 font-medium`}>
                            {bug.category}
                          </span>
                        </>
                      )}

                      <span className="text-gray-200">·</span>
                      <span className={`text-[11px] text-gray-400`}>
                        {bug.filesChanged} file{bug.filesChanged !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>

                  {/* Chevron */}
                  <div className="flex-shrink-0 self-center text-gray-300 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-blue-500 transition-all duration-150">
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}