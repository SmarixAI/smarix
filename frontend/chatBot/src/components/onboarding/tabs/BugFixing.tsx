'use client';

import { useEffect, useMemo, useState } from 'react';
import { BookOpen, Code2, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

type FilterType = 'all' | 'tutorials' | 'challenges';

interface BugFixingProps {
  activeRepos?: string[];
  employeeId?: string | null;
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
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
  category?: string;
}

export default function BugFixing({ 
  activeRepos = [],
  employeeId,
  onboardingData,
  onUpdateProgress
}: BugFixingProps) {
  const router = useRouter();

  const [tutorials, setTutorials] = useState<any>(null);
  const [challenges, setChallenges] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [search, setSearch] = useState('');

  /* ===================== FETCH ===================== */

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const repo = activeRepos[0];
      const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';

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
        console.error('Error fetching bug fix data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeRepos]);

  /* ===================== DATA PROCESSING ===================== */

  const bugs: BugListItem[] = useMemo(() => {
    // 1. Process Tutorials
    const rawTutorials = tutorials?.tutorials || [];
    
    const tutorialItems = rawTutorials.map((t: any) => {
      // Fallback: If pr_title is missing, try to scrape it from markdown raw_response
      let title = t.pr_title;
      if (!title && t.raw_response) {
        const match = t.raw_response.match(/^#\s*Tutorial.*?:(.+?)$/m);
        if (match) title = match[1].trim();
      }

      // Fallback description
      let description = t.brief_description;
      if (!description && t.raw_response) {
        const match = t.raw_response.match(/##\s*1\.?\s*Overview\s*\n+([\s\S]*?)(?=\n##)/);
        if (match) description = match[1].trim().slice(0, 150) + '...';
      }

      return {
        id: t.tutorial_number,
        type: 'tutorial' as const,
        title: title || `Tutorial for PR #${t.pr_number}`,
        description: description || 'Learn how this PR was implemented.',
        difficulty: (t.difficulty || 'Medium') as 'Easy' | 'Medium' | 'Hard',
        prNumber: t.pr_number,
        filesChanged: t.code_files_modified || 0,
      };
    });

    // 2. Process Challenges (Parsing raw_response JSON)
    const rawChallenges = challenges?.questions || [];

    const challengeItems = rawChallenges.map((c: any) => {
      let parsedContent: any = {};
      try {
        // The raw_response is often a JSON string in these challenges
        parsedContent = typeof c.raw_response === 'string' 
          ? JSON.parse(c.raw_response) 
          : c.raw_response;
      } catch (e) {
        // Fallback if not valid JSON
        parsedContent = { title: "Coding Challenge", problem: c.raw_response };
      }

      return {
        id: c.question_number,
        type: 'challenge' as const,
        title: parsedContent.title || `Challenge #${c.question_number}`,
        description: parsedContent.problem 
          ? (parsedContent.problem.slice(0, 120) + '...') 
          : 'Solve the coding problem.',
        difficulty: 'Medium', // Challenges usually default to Medium
        prNumber: c.question_number, 
        filesChanged: 1,
        category: c.category
      };
    });

    // 3. Filter & Search
    return [...tutorialItems, ...challengeItems].filter(item => {
      if (filter === 'tutorials' && item.type !== 'tutorial') return false;
      if (filter === 'challenges' && item.type !== 'challenge') return false;
      
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

  const handleBugClick = (bug: BugListItem) => {
    router.push(`/employee/onboarding/bug-fix/${bug.type}/${bug.id}`);
  };

  return (
    <div className={`${inter.className} h-full flex flex-col bg-[#FAFAFA]`}>
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
                placeholder="Search bugs, PRs..."
                className="w-full pl-9 pr-4 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* LIST */}
      <div className="flex-1 overflow-y-auto px-0 py-4">
        <div className="bg-white border border-slate-200 divide-y divide-slate-200 rounded-xl overflow-hidden mx-6">
          {bugs.map((bug, idx) => (
            <div
              key={`${bug.type}-${bug.id}`}
              onClick={() => handleBugClick(bug)}
              className="group relative px-6 py-5 cursor-pointer transition hover:bg-slate-50"
            >
              <div className="flex gap-5">
                {/* Icon */}
                {bug.type === 'tutorial' ? (
                  <div className="mt-1 p-2 rounded-lg bg-blue-50 group-hover:bg-blue-100 transition-colors">
                    <BookOpen className="w-5 h-5 text-blue-600" />
                  </div>
                ) : (
                  <div className="mt-1 p-2 rounded-lg bg-amber-50 group-hover:bg-amber-100 transition-colors">
                    <Code2 className="w-5 h-5 text-amber-600" />
                  </div>
                )}

                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2.5 py-0.5 rounded text-xs font-medium ${TYPE_STYLES[bug.type]}`}>
                      {bug.type === 'tutorial' ? 'Tutorial' : 'Challenge'}
                    </span>

                    {/* Category Tag for Challenges */}
                    {bug.category && (
                      <span className="px-2.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                        {bug.category}
                      </span>
                    )}

                    <p className="text-sm font-semibold text-slate-900">
                      #{bug.id} · {bug.title}
                    </p>
                  </div>

                  <p className="text-sm text-slate-600 leading-relaxed max-w-4xl line-clamp-2">
                    {bug.description}
                  </p>

                  <div className="flex items-center gap-4 text-xs pt-1">
                    <span className={`px-2 py-0.5 rounded font-medium ${DIFFICULTY_STYLES[bug.difficulty]}`}>
                      {bug.difficulty}
                    </span>

                    {bug.type === 'tutorial' && (
                      <span className="text-slate-500">
                        {bug.filesChanged} file{bug.filesChanged !== 1 && 's'} changed
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {bugs.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-500">
              No bugs found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}