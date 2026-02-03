"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Code2,
  Sparkles,
  ChevronRight,
  AlertCircle,
  Shield,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Inter } from "next/font/google";
// ✅ Import Auth
import { useAuth } from "@/components/auth/AuthContext";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

type FilterType = "all" | "tutorials" | "challenges";

interface BugFixingProps {
  activeRepos?: string[];
  employeeId?: string | null;
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

/* ===================== UI HELPERS ===================== */

const DIFFICULTY_STYLES: Record<string, string> = {
  Easy: "bg-green-100 text-green-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Hard: "bg-red-100 text-red-700",
};

const TYPE_STYLES: Record<"tutorial" | "challenge", string> = {
  tutorial: "bg-blue-100 text-blue-700",
  challenge: "bg-amber-100 text-amber-700",
};

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

export default function BugFixing({
  activeRepos: propActiveRepos = [],
  employeeId,
  onboardingData,
  onUpdateProgress,
}: BugFixingProps) {
  const router = useRouter();
  const { user } = useAuth();

  // ✅ Resolve Active Repo (Props -> Context -> Empty)
  const activeRepos =
    propActiveRepos.length > 0 ? propActiveRepos : user?.activeRepos || [];
  const currentRepo = activeRepos[0] || "";

  const [tutorials, setTutorials] = useState<any>(null);
  const [challenges, setChallenges] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [missingRepo, setMissingRepo] = useState(false);
  const [filter, setFilter] = useState<FilterType>("all");
  const [search, setSearch] = useState("");

  /* ===================== FETCH ===================== */

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setMissingRepo(false);

      // ✅ Guard Clause: No Repo
      if (!currentRepo) {
        setMissingRepo(true);
        setLoading(false);
        return;
      }

      const repoParam = `?repo=${encodeURIComponent(currentRepo)}`;

      try {
        // Fetch from the two separate API endpoints
        const [tutRes, chalRes] = await Promise.all([
          fetch(`/api/onboarding/bugFix/tutorials${repoParam}`),
          fetch(`/api/onboarding/bugFix/challenges${repoParam}`),
        ]);

        if (tutRes.ok) {
          const tutData = await tutRes.json();
          setTutorials(tutData);
        }
        if (chalRes.ok) {
          const chalData = await chalRes.json();
          setChallenges(chalData);
        }
      } catch (error) {
        console.error("Error fetching bug fix data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentRepo]);

  /* ===================== DATA PROCESSING ===================== */

  const bugs: BugListItem[] = useMemo(() => {
    // 1. Process Tutorials
    const rawTutorials = tutorials?.tutorials || [];

    const tutorialItems = rawTutorials.map((t: any) => {
      let title = t.pr_title;
      if (!title && t.raw_response) {
        const match = t.raw_response.match(/^#\s*Tutorial.*?:(.+?)$/m);
        if (match) title = match[1].trim();
      }

      let description = t.brief_description;
      if (!description && t.raw_response) {
        const match = t.raw_response.match(
          /##\s*1\.?\s*Overview\s*\n+([\s\S]*?)(?=\n##)/,
        );
        if (match) description = match[1].trim().slice(0, 150) + "...";
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

    // 2. Process Challenges
    const rawChallenges = challenges?.questions || [];

    const challengeItems = rawChallenges.map((c: any) => {
      let parsedContent: any = {};
      try {
        parsedContent =
          typeof c.raw_response === "string"
            ? JSON.parse(c.raw_response)
            : c.raw_response;
      } catch (e) {
        parsedContent = { title: "Coding Challenge", problem: c.raw_response };
      }

      return {
        id: c.question_number,
        type: "challenge" as const,
        title: parsedContent.title || `Challenge #${c.question_number}`,
        description: parsedContent.problem
          ? parsedContent.problem.slice(0, 120) + "..."
          : "Solve the coding problem.",
        difficulty: "Medium",
        prNumber: c.question_number,
        filesChanged: 1,
        category: c.category,
      };
    });

    // 3. Filter & Search
    return [...tutorialItems, ...challengeItems].filter((item) => {
      if (filter === "tutorials" && item.type !== "tutorial") return false;
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

  /* ===================== RENDER ===================== */

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full min-h-[400px]">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  // ✅ Missing Repo UI
  if (missingRepo) {
    return (
      <div className="flex h-full min-h-[400px] flex-col items-center justify-center p-12 text-center bg-[#FAFAFA]">
        <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center mb-4 border border-amber-100">
          <AlertCircle className="w-8 h-8 text-amber-500" />
        </div>
        <h3 className={`${inter.className} text-lg font-bold text-slate-800`}>
          No Repository Assigned
        </h3>
        <p
          className={`${inter.className} text-sm text-slate-500 mt-2 max-w-xs leading-relaxed`}
        >
          Bug fixing tasks are specific to your project. Please ask your manager
          to assign an active repository.
        </p>
      </div>
    );
  }

  const handleBugClick = (bug: BugListItem) => {
    // Navigate to detail view
    router.push(`/employee/onboarding/bug-fix/${bug.type}/${bug.id}`);
  };

  return (
    <div className={`${inter.className} h-auto flex flex-col bg-[#FAFAFA] relative no-scrollbar`}>
      {/* HEADER */}
      <div className="sticky top-0 z-20 bg-gradient-to-b from-white to-[#FAFAFA] border-b border-slate-200 flex-shrink-0">
        <div className="px-6 pt-5 pb-3">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Bug Fix Training
          </h1>
          <p className="text-sm text-slate-600">
            Debug real-world pull requests like production issues
          </p>
        </div>

        {/* Filters */}
        <div className="px-6 pb-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
              {(["all", "tutorials", "challenges"] as FilterType[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-1.5 text-sm rounded-lg transition font-medium ${
                    filter === f
                      ? "bg-[#0E1B2E] shadow-sm text-white"
                      : "text-slate-500 hover:text-slate-700 mx-2"
                  }`}
                >
                  {f === "all"
                    ? "All"
                    : f === "tutorials"
                      ? "Tutorials"
                      : "Challenges"}
                </button>
              ))}
            </div>

            <div className="relative w-72">
              <Sparkles className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search bugs, PRs..."
                className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* LIST */}
      <div className="flex-1 px-0 py-3 bg-slate-50/50">
        <div className="max-h-[65vh] overflow-y-auto mx-6 bg-white border border-slate-200 rounded-2xl shadow-sm divide-y divide-slate-100 no-scrollbar">
          {bugs.map((bug) => (
            <div
              key={`${bug.type}-${bug.id}`}
              onClick={() => handleBugClick(bug)}
              className="group relative px-6 py-5 cursor-pointer transition-all duration-200 hover:bg-blue-50/30 flex items-start gap-5"
            >
              <div
                className={`mt-1 p-2.5 rounded-xl transition-colors ${
                  bug.type === "tutorial"
                    ? "bg-blue-50 text-blue-600 group-hover:bg-blue-100"
                    : "bg-amber-50 text-amber-600 group-hover:bg-amber-100"
                }`}
              >
                {bug.type === "tutorial" ? (
                  <BookOpen className="w-5 h-5" />
                ) : (
                  <Code2 className="w-5 h-5" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4 mb-1">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-medium text-slate-400">
                        #{bug.id}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 truncate group-hover:text-blue-700 transition-colors">
                        {bug.title}
                      </h3>
                    </div>
                    <p className="text-sm text-slate-500 line-clamp-1 leading-relaxed">
                      {bug.description}
                    </p>
                  </div>

                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span
                        className={`px-2 py-1 rounded-full text-[10px] tracking-wider font-bold border flex items-center justify-center w-15 h-[18px] ${
                          DIFFICULTY_STYLES[bug.difficulty]
                        }`}
                      >
                        {bug.difficulty}
                      </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-3">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs justify-center font-medium ${TYPE_STYLES[bug.type]} w-20`}
                  >
                    {bug.type === "tutorial" ? "Tutorial" : "Challenge"}
                  </span>
                  {bug.category && (
                    <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                      <span className="w-1 h-1 rounded-full bg-slate-300" />
                      {bug.category}
                    </span>
                  )}
                </div>
              </div>

              <div className="self-center opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-slate-300">
                <ChevronRight className="w-5 h-5" />
              </div>
            </div>
          ))}

          {bugs.length === 0 && (
            <div className="py-16 text-center flex flex-col items-center">
              <Shield className="w-10 h-10 text-slate-200 mb-2" />
              <p className="text-sm text-slate-400 font-medium">
                No items found.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
