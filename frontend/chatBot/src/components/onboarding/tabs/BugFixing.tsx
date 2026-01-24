'use client';

import { useEffect, useMemo, useState } from 'react';
import { BookOpen, Code2, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import type {
  PRTutorialsResponse,
  CodingQuestionsResponse,
} from '../../../../types/onboarding';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

type FilterType = 'all' | 'tutorials' | 'challenges';

interface BugFixingProps {
  activeRepos?: string[];
}

/* ===================== UI HELPERS ===================== */

const DIFFICULTY_STYLES: Record<string, string> = {
  Easy: 'bg-green-100 text-green-700',
  Medium: 'bg-yellow-100 text-yellow-700',
  Hard: 'bg-red-100 text-red-700',
};

const TYPE_STYLES: Record<'tutorial' | 'challenge', string> = {
  tutorial: 'bg-blue-100 text-blue-700',
  challenge: 'bg-amber-100 text-amber-700',
};

interface BugListItem {
  id: number;
  type: 'tutorial' | 'challenge';
  title: string;
  description: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  prNumber: number;
  filesChanged: number;
}

export default function BugFixing({ activeRepos = [] }: BugFixingProps) {
  const router = useRouter();

  const [tutorials, setTutorials] =
    useState<PRTutorialsResponse | null>(null);
  const [challenges, setChallenges] =
    useState<CodingQuestionsResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);

  /* ===================== FETCH ===================== */

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const repo = activeRepos[0];
      const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';

      try {
        const [tutRes, chalRes] = await Promise.all([
          fetch(`/api/onboarding/bugFix/tutorials${repoParam}`),
          fetch(`/api/onboarding/bugFix/challenges${repoParam}`),
        ]);

        if (tutRes.ok) setTutorials(await tutRes.json());
        if (chalRes.ok) setChallenges(await chalRes.json());
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeRepos]);

  /* ===================== DATA ===================== */

  const bugs: BugListItem[] = useMemo(() => {
    const tutorialItems =
      tutorials?.tutorials.map(t => ({
        id: t.tutorial_number,
        type: 'tutorial',
        title: t.pr_title,
        description: t.brief_description,
        difficulty: t.difficulty ?? 'Easy',
        prNumber: t.pr_number,
        filesChanged: t.code_files_modified,
      })) ?? [];

    const challengeItems =
      challenges?.questions.map(c => ({
        id: c.pr_number,
        type: 'challenge',
        title: `Fix issues in PR #${c.pr_number}`,
        description:
          c.file_changes?.length
            ? `Resolve code issues across ${c.file_changes.length} modified file(s).`
            : 'Resolve the reported code issues in this pull request.',
        difficulty: 'Medium',
        prNumber: c.pr_number,
        filesChanged: c.file_changes?.length ?? 0,
      })) ?? [];

    return [...tutorialItems, ...challengeItems].filter(item => {
      if (filter === 'tutorials' && item.type !== 'tutorial') return false;
      if (filter === 'challenges' && item.type !== 'challenge') return false;
      if (search)
        return (
          item.title.toLowerCase().includes(search.toLowerCase()) ||
          item.description.toLowerCase().includes(search.toLowerCase())
        );
      return true;
    });
  }, [tutorials, challenges, filter, search]);

  /* ===================== LOADING ===================== */

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  /* ===================== UI ===================== */

  return (
    <div className={`${inter.className} h-full flex flex-col bg-[#FAFAFA]`}>
      {/* ================= HEADER ================= */}
      <div className="sticky top-0 z-20 bg-gradient-to-b from-white to-[#FAFAFA] border-b border-slate-200">
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
            <div className="flex bg-slate-100 p-1 rounded-xl">
              {(['all', 'tutorials', 'challenges'] as FilterType[]).map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-1.5 text-sm rounded-lg transition font-medium ${
                    filter === f
                      ? 'bg-white shadow-sm text-slate-900'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {f === 'all'
                    ? 'All'
                    : f === 'tutorials'
                    ? 'Tutorials'
                    : 'Challenges'}
                </button>
              ))}
            </div>

            <div className="relative w-72">
              <Sparkles className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search bugs, PRs, descriptions"
                className="w-full pl-9 pr-4 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* ================= LIST ================= */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="bg-white border rounded-xl divide-y">
          {bugs.map((bug, idx) => (
            <div
              key={`${bug.type}-${bug.id}`}
              onClick={() =>
                router.push(
                  bug.type === 'tutorial'
                    ? `/bug-fix/tutorial/${bug.id}`
                    : `/bug-fix/challenge/${bug.id}`
                )
              }
              className={`group relative px-6 py-5 cursor-pointer transition ${
                idx === activeIndex
                  ? 'bg-blue-50'
                  : 'hover:bg-slate-50'
              }`}
            >
              {/* Left accent */}
              <div
                className={`absolute left-0 top-0 h-full w-1 rounded-r ${
                  idx === activeIndex
                    ? 'bg-blue-500'
                    : 'bg-transparent group-hover:bg-slate-300'
                }`}
              />

              <div className="flex gap-5">
                {bug.type === 'tutorial' ? (
                  <BookOpen className="w-6 h-6 text-blue-600 mt-1" />
                ) : (
                  <Code2 className="w-6 h-6 text-amber-600 mt-1" />
                )}

                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`px-2.5 py-0.5 rounded text-xs font-medium ${TYPE_STYLES[bug.type]}`}
                    >
                      {bug.type === 'tutorial' ? 'Tutorial' : 'Challenge'}
                    </span>

                    <p className="text-sm font-semibold text-slate-900">
                      PR #{bug.prNumber} · {bug.title}
                    </p>
                  </div>

                  <p className="text-sm text-slate-600 leading-relaxed max-w-4xl">
                    {bug.description}
                  </p>

                  <div className="flex items-center gap-4 text-xs pt-1">
                    <span
                      className={`px-2 py-0.5 rounded ${DIFFICULTY_STYLES[bug.difficulty]}`}
                    >
                      {bug.difficulty}
                    </span>

                    <span className="text-slate-500">
                      {bug.filesChanged} file
                      {bug.filesChanged !== 1 && 's'} changed
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {bugs.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-500">
              No bugs found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
