'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, BookOpen, Lightbulb, CheckCircle2, Clock, Code2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Inter, JetBrains_Mono } from 'next/font/google';
import CodeEditor from '@/components/onboarding/utils/BugFix/CodeEditor';
import ContentSection from '@/components/onboarding/utils/BugFix/ContentSection';
import StepByStepSection from '@/components/onboarding/utils/BugFix/StepByStepSection';
import EvaluationModal from '@/components/onboarding/utils/BugFix/EvaluationModal';
import { parseTutorialContent } from '@/components/onboarding/utils/BugFix/contentParser';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

export default function BugFixDetailPage() {
  const params = useParams();
  const router = useRouter();
  const type = params.type as string;
  const id = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);
  const [activeRepos, setActiveRepos] = useState<string[]>([]);
  const [challengeSolutionData, setChallengeSolutionData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'description' | 'hints' | 'solution'>('description');
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [challengePrData, setChallengePrData] = useState<any>(null);

  useEffect(() => {
    const fetchActiveRepos = async () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          let repos = user.active_repos || [];
          
          // If no active_repos in localStorage, try to fetch from API
          if (!repos || repos.length === 0) {
            const usersRes = await fetch('/api/users');
            if (usersRes.ok) {
              const usersData = await usersRes.json();
              const currentUser = usersData.users?.find((u: any) => 
                u.employeeId === user.employeeId || 
                u.username === user.username || 
                u.name === user.username
              );
              if (currentUser?.active_repos) {
                repos = currentUser.active_repos;
              }
            }
          }
          
          setActiveRepos(repos);
        }
      } catch (error) {
        console.error('Error fetching active repos:', error);
      }
    };

    fetchActiveRepos();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
        const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';

        let response;
        if (type === 'tutorial') {
          response = await fetch(`/api/onboarding/bugFix/tutorials/${id}${repoParam}`);
        } else {
          response = await fetch(`/api/onboarding/bugFix/challenges/${id}${repoParam}`);
        }

        if (!response.ok) {
          throw new Error('Failed to fetch bug fix data');
        }

        const result = await response.json();
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load bug fix details');
      } finally {
        setLoading(false);
      }
    };

    // Fetch data once activeRepos is set (even if empty)
    fetchData();
  }, [type, id, activeRepos.length]);

  // Fetch challenge solution data for challenges - MUST be before early returns
  useEffect(() => {
    if (type === 'challenge') {
      const fetchSolutionData = async () => {
        try {
          const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
          const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';
          const response = await fetch(`/api/onboarding/bugFix/solutions${repoParam}`);
          if (response.ok) {
            const solutionData = await response.json();
            setChallengeSolutionData(solutionData);
          }
        } catch (error) {
          console.error('Error fetching challenge solution data:', error);
        }
      };
      // Fetch even if no activeRepos (will try to find data anyway)
      fetchSolutionData();
    }
  }, [type, activeRepos]);

  // Update challenge prData when challengeSolutionData or data changes
  // Uses tutorial_number as primary matching key (new field added by user)
  useEffect(() => {
    if (type === 'challenge' && data) {
      console.log('🔍 Processing challenge data:', {
        id,
        tutorial_number: data.tutorial_number,
        pr_number: data.pr_number,
        question_number: data.question_number,
        has_file_changes: !!data.file_changes,
        file_changes_count: data.file_changes?.length || 0,
        has_solution_data: !!challengeSolutionData,
        solution_prs_count: challengeSolutionData?.pull_requests?.length || 0,
      });
      
      // First, check if challenge has file_changes directly (most reliable)
      if (data.file_changes && Array.isArray(data.file_changes) && data.file_changes.length > 0) {
        const prNumber = data.pr_number || data.question_number || parseInt(id) || 0;
        const computedPrData = {
          pr_number: prNumber,
          file_changes: data.file_changes.map((file: any) => ({
            file_path: file.filename || file.path || file.file_path,
            change_type: file.status || file.change_type || 'modified',
            diff: file.patch || file.diff || '',
            before_code: file.before_code || file.content || file.before || '',
            after_code: file.after_code || file.after || '',
            statistics: {
              lines_added: file.additions || 0,
              lines_deleted: file.deletions || 0,
              total_changes: (file.additions || 0) + (file.deletions || 0),
            },
          })),
        };
        setChallengePrData(computedPrData);
        console.log('✅ Challenge prData from file_changes:', computedPrData);
        return;
      }
      
      // If no file_changes in challenge data, try to find in solution data
      if (challengeSolutionData && challengeSolutionData.pull_requests) {
        // PRIORITY 1: Match by tutorial_number (new field - most reliable)
        if (data.tutorial_number) {
          const prByTutorialNumber = challengeSolutionData.pull_requests.find(
            (p: any) => p.tutorial_number === data.tutorial_number
          );
          if (prByTutorialNumber && prByTutorialNumber.file_changes && prByTutorialNumber.file_changes.length > 0) {
            setChallengePrData(prByTutorialNumber);
            console.log('✅ Challenge prData from solution data (tutorial_number match):', prByTutorialNumber);
            return;
          }
        }
        
        // PRIORITY 2: Extract PR number from raw_response and match
        if (data.raw_response) {
          const prMatch = data.raw_response.match(/Issue\/PR\s*#?(\d+)/i);
          if (prMatch) {
            const prNumber = parseInt(prMatch[1]);
            const pr = challengeSolutionData.pull_requests.find(
              (p: any) => p.pr_number === prNumber
            );
            if (pr && pr.file_changes && pr.file_changes.length > 0) {
              setChallengePrData(pr);
              console.log('✅ Challenge prData from solution data (raw_response match):', pr);
              return;
            }
          }
        }
        
        // PRIORITY 3: Direct pr_number match
        if (data.pr_number) {
          const pr = challengeSolutionData.pull_requests.find(
            (p: any) => p.pr_number === data.pr_number
          );
          if (pr && pr.file_changes && pr.file_changes.length > 0) {
            setChallengePrData(pr);
            console.log('✅ Challenge prData from solution data (pr_number match):', pr);
            return;
          }
        }
        
        // PRIORITY 4: question_number match
        if (data.question_number) {
          const pr = challengeSolutionData.pull_requests.find(
            (p: any) => p.pr_number === data.question_number || p.tutorial_number === data.question_number
          );
          if (pr && pr.file_changes && pr.file_changes.length > 0) {
            setChallengePrData(pr);
            console.log('✅ Challenge prData from solution data (question_number match):', pr);
            return;
          }
        }
        
        // PRIORITY 5: ID match (try both pr_number and tutorial_number)
        const prById = challengeSolutionData.pull_requests.find(
          (p: any) => p.pr_number === parseInt(id) || p.tutorial_number === parseInt(id)
        );
        if (prById && prById.file_changes && prById.file_changes.length > 0) {
          setChallengePrData(prById);
          console.log('✅ Challenge prData from solution data (ID match):', prById);
          return;
        }
        
        // PRIORITY 6: Use first available PR with file_changes
        const prWithFiles = challengeSolutionData.pull_requests.find(
          (p: any) => p.file_changes && Array.isArray(p.file_changes) && p.file_changes.length > 0
        );
        if (prWithFiles) {
          setChallengePrData(prWithFiles);
          console.log('✅ Challenge prData from solution data (first with files):', prWithFiles);
          return;
        }
      }
      
      // If still nothing after checking solution data, log for debugging
      console.log('⚠️ No file_changes found. Challenge data keys:', Object.keys(data || {}));
      if (challengeSolutionData) {
        console.log('⚠️ Available PRs in solution:', challengeSolutionData.pull_requests?.map((p: any) => ({
          pr_number: p.pr_number,
          tutorial_number: p.tutorial_number,
          file_changes_count: p.file_changes?.length || 0
        })));
      }
      
      // Don't set empty file_changes - let CodeEditor show its own "No PR data" message
    } else if (type === 'challenge' && !data) {
      setChallengePrData(null);
    }
  }, [type, data, challengeSolutionData, id]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const container = document.querySelector('.bugfix-detail-container');
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftPanelWidth(Math.max(20, Math.min(80, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Failed to load data'}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Parse tutorial content if it's a tutorial
  const parsedContent = type === 'tutorial' && data.raw_response 
    ? parseTutorialContent(data.raw_response) 
    : null;

  // Get PR data for code editor
  // For tutorials, use file_changes directly
  // For challenges, use challengePrData from useEffect
  let prData: any = null;
  
  if (type === 'tutorial') {
    prData = data.file_changes ? {
      pr_number: data.pr_number || data.tutorial_number || parseInt(id),
      file_changes: data.file_changes.map((file: any) => ({
        file_path: file.filename || file.path || file.file_path,
        change_type: file.status || 'modified',
        diff: file.patch || '',
        before_code: file.before_code || file.content || '',
        after_code: file.after_code || '',
        statistics: {
          lines_added: file.additions || 0,
          lines_deleted: file.deletions || 0,
          total_changes: (file.additions || 0) + (file.deletions || 0),
        },
      })),
    } : null;
  } else if (type === 'challenge') {
    // Use the computed challengePrData from useEffect
    prData = challengePrData;
  }

  // Challenge-specific data extraction
  const challengeContent = type === 'challenge' && data.raw_response 
    ? data.raw_response.split('**Solution**')[0] 
    : '';
  const difficultyMatch = type === 'challenge' && data.raw_response 
    ? data.raw_response.match(/Difficulty:\s*(\w+)/i) 
    : null;
  const timeMatch = type === 'challenge' && data.raw_response 
    ? data.raw_response.match(/Estimated time:\s*([^\n]+)/i) 
    : null;
  const prMatch = type === 'challenge' && data.raw_response
    ? data.raw_response.match(/Issue\/PR\s*#?(\d+)/i)
    : null;
  const skillsMatch = type === 'challenge' && data.raw_response
    ? data.raw_response.match(/Skills tested:\s*([\s\S]*?)(?:\n\n|\n##|$)/i)
    : null;

  const difficulty = difficultyMatch?.[1] || data.difficulty || 'Medium';
  const time = timeMatch?.[1] || '30-60 min';
  const prNumber = prMatch?.[1] || data.pr_number || data.question_number || id;
  
  // Extract skills from the content
  const skills = skillsMatch?.[1]
    ? skillsMatch[1]
        .split('\n')
        .map((line: string) => line.trim().replace(/^[-•]\s*/, ''))
        .filter((line: string) => line.length > 0)
    : [];

  const getDifficultyColor = (diff: string) => {
    const lower = diff.toLowerCase();
    if (lower === 'easy') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (lower === 'hard') return 'bg-rose-50 text-rose-700 border-rose-200';
    return 'bg-amber-50 text-amber-700 border-amber-200';
  };

  const handleEvaluationComplete = (evalData: any) => {
    setEvaluationData(evalData);
    setShowEvaluationModal(true);
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* Header with back button */}
      <div className="sticky top-0 z-30 bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition mb-3 group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Bug Fix List</span>
        </button>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-2">
              {data.pr_title || `PR #${data.pr_number || id}`}
            </h1>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                {type === 'tutorial' ? 'Tutorial' : 'Challenge'}
              </span>
              {data.difficulty && (
                <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${getDifficultyColor(data.difficulty)}`}>
                  {data.difficulty}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="h-[calc(100vh-120px)] flex gap-0 bugfix-detail-container relative rounded-2xl border-2 border-[#0E1B2E]/10 overflow-hidden bg-white shadow-xl shadow-[#0E1B2E]/5">
        {/* Left Panel - Problem Details */}
        <div
          className={`flex flex-col relative bg-white overflow-hidden ${
            type === 'challenge' && isFullscreen ? 'hidden' : ''
          }`}
          style={{ width: `${leftPanelWidth}%` }}
        >
          {type === 'challenge' ? (
            <>
              {/* Header */}
              <div className="px-6 py-5 border-b border-[#0E1B2E]/10 bg-gradient-to-r from-white to-slate-50/50 flex-shrink-0">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span
                      className={`${jetbrainsMono.className} text-xs font-bold text-[#0E1B2E]/60 bg-[#0E1B2E]/10 px-2.5 py-1 rounded-md border border-[#0E1B2E]/10`}
                    >
                      #{data.question_number || data.pr_number || id}
                    </span>
                    <h1
                      className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}
                    >
                      Problem Statement
                    </h1>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`${inter.className} inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide border ${getDifficultyColor(difficulty)}`}
                    >
                      {difficulty}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap mb-4">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-[#0E1B2E]/70 bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{time}</span>
                  </div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-[#0E1B2E]/70 bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                    <Code2 className="w-3.5 h-3.5" />
                    <span>{data.category || 'Bug Fix'}</span>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex p-1 bg-[#0E1B2E]/5 rounded-lg border border-[#0E1B2E]/5">
                  {[
                    { id: 'description', label: 'Description', icon: BookOpen },
                    { id: 'hints', label: 'Hints', icon: Lightbulb },
                    { id: 'solution', label: 'Solution', icon: CheckCircle2 },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-bold transition-all duration-200 ${
                        activeTab === tab.id
                          ? 'bg-white text-[#0E1B2E] shadow-sm ring-1 ring-[#0E1B2E]/5'
                          : 'text-[#0E1B2E]/60 hover:text-[#0E1B2E] hover:bg-[#0E1B2E]/5'
                      }`}
                    >
                      <tab.icon className="w-3.5 h-3.5" />
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto px-8 py-6 bg-slate-50/50">
                  {activeTab === 'description' && (
                    <div className="max-w-none">
                      {/* Challenge Overview Section */}
                      <div className="mb-6 p-5 bg-white rounded-xl border border-[#0E1B2E]/10 shadow-sm">
                        <h2 className={`${inter.className} text-base font-bold text-[#0E1B2E] mb-4 flex items-center gap-2`}>
                          <div className="w-1 h-5 bg-[#0E1B2E] rounded-full" />
                          Challenge Overview
                        </h2>
                        <div className="space-y-3 text-sm">
                          {prMatch && (
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-[#0E1B2E]/80 min-w-[120px]">Question:</span>
                              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium text-[#0E1B2E]/70 bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                                Based on Issue/PR #{prNumber}
                              </span>
                            </div>
                          )}
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-[#0E1B2E]/80 min-w-[120px]">Difficulty:</span>
                            <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${getDifficultyColor(difficulty)}`}>
                              {difficulty}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-[#0E1B2E]/80 min-w-[120px]">Estimated time:</span>
                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium text-[#0E1B2E]/70 bg-[#0E1B2E]/5 border border-[#0E1B2E]/10">
                              {time}
                            </span>
                          </div>
                          {skills.length > 0 && (
                            <div className="flex items-start gap-2">
                              <span className="font-semibold text-[#0E1B2E]/80 min-w-[120px] pt-1">Skills tested:</span>
                              <div className="flex flex-wrap gap-2">
                                {skills.map((skill: string, idx: number) => (
                                  <span
                                    key={idx}
                                    className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200"
                                  >
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Problem Description Section */}
                      <div className="prose prose-sm max-w-none prose-slate">
                        <ReactMarkdown
                          components={{
                          code(props) {
                            const { children, className } = props;
                            const match = /language-(\w+)/.exec(className || '');
                            return match ? (
                              <div className="my-4 rounded-xl overflow-hidden border border-[#0E1B2E]/10 shadow-sm bg-white">
                                <div className="px-3 py-1.5 bg-[#0E1B2E]/5 border-b border-[#0E1B2E]/5 flex items-center justify-between">
                                  <span
                                    className={`${jetbrainsMono.className} text-[10px] font-bold text-[#0E1B2E]/60 uppercase`}
                                  >
                                    {match[1]}
                                  </span>
                                </div>
                                <SyntaxHighlighter
                                  PreTag="div"
                                  language={match[1]}
                                  style={oneLight}
                                  customStyle={{
                                    margin: 0,
                                    padding: '1rem',
                                    fontSize: '0.85rem',
                                    background: 'white',
                                  }}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              </div>
                            ) : (
                              <code
                                className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded text-[13px] bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/10`}
                              >
                                {children}
                              </code>
                            );
                          },
                          h1: ({ children }) => (
                            <h1
                              className={`${inter.className} text-xl font-bold mb-4 pb-3 border-b-2 border-[#0E1B2E]/20 text-[#0E1B2E] mt-8 first:mt-0`}
                            >
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2
                              className={`${inter.className} text-lg font-bold mb-3 mt-6 text-[#0E1B2E] flex items-center gap-2`}
                            >
                              <div className="w-1 h-5 bg-[#0E1B2E] rounded-full" />
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3
                              className={`${inter.className} text-base font-semibold mb-2 mt-4 text-[#0E1B2E]/90`}
                            >
                              {children}
                            </h3>
                          ),
                          p: ({ children }) => (
                            <p
                              className={`${inter.className} mb-4 leading-relaxed text-[15px] text-[#0E1B2E]/80`}
                            >
                              {children}
                            </p>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc list-outside mb-4 space-y-2 ml-5 text-[#0E1B2E]/80">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal list-outside mb-4 space-y-2 ml-5 text-[#0E1B2E]/80">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li
                              className={`${inter.className} leading-relaxed text-[15px]`}
                            >
                              {children}
                            </li>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-blue-500/40 bg-blue-50/60 pl-4 py-3 pr-4 rounded-r my-4 text-[#0E1B2E]/80 italic">
                              {children}
                            </blockquote>
                          ),
                          strong: ({ children }) => (
                            <strong className={`${inter.className} font-semibold text-[#0E1B2E]`}>
                              {children}
                            </strong>
                          ),
                        }}
                      >
                        {challengeContent || data.brief_description || data.description || 'No description available.'}
                      </ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {activeTab === 'hints' && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-6">
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                          <Lightbulb className="w-4 h-4 text-amber-600" />
                        </div>
                        <div>
                          <h4
                            className={`${inter.className} font-bold text-[#0E1B2E] mb-3`}
                          >
                            Helpful Hints
                          </h4>
                          <ul className="space-y-3">
                            {[
                              'Carefully read through the problem description and understand the requirements',
                              'Look at the file structure and identify which files need to be modified',
                              'Test your changes with different scenarios and edge cases',
                              'Make sure your code follows best practices and is well-documented',
                            ].map((hint, i) => (
                              <li
                                key={i}
                                className="flex gap-3 text-sm text-[#0E1B2E]/70"
                              >
                                <span className="text-amber-500 mt-0.5">•</span>
                                <span>{hint}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'solution' && (
                    <div className="rounded-xl border border-[#0E1B2E]/10 bg-slate-50 p-8 text-center">
                      <div className="w-12 h-12 rounded-xl bg-[#0E1B2E]/5 flex items-center justify-center mx-auto mb-4">
                        <CheckCircle2 className="w-6 h-6 text-[#0E1B2E]/40" />
                      </div>
                      <h4
                        className={`${inter.className} font-bold text-[#0E1B2E] mb-2`}
                      >
                        Solution Hidden
                      </h4>
                      <p
                        className={`${inter.className} text-sm text-[#0E1B2E]/60 max-w-sm mx-auto`}
                      >
                        Try to solve the challenge on your own first! The solution
                        will be revealed after you attempt the challenge.
                      </p>
                    </div>
                  )}
              </div>
            </>
          ) : type === 'tutorial' && parsedContent ? (
            <div className="flex-1 overflow-y-auto px-8 py-6 bg-slate-50/50">
              <div className="max-w-4xl mx-auto space-y-8">
                {/* Left side content for tutorials */}
                {parsedContent.overview && (
                  <ContentSection title="Overview" content={parsedContent.overview} />
                )}
                {parsedContent.problemContext && (
                  <ContentSection title="Problem Context" content={parsedContent.problemContext} />
                )}
                {parsedContent.testing && (
                  <ContentSection title="Testing Strategy" content={parsedContent.testing} />
                )}
                {parsedContent.keyTakeaways && (
                  <ContentSection title="Key Takeaways" content={parsedContent.keyTakeaways} />
                )}
                {parsedContent.practiceExercises && (
                  <ContentSection title="Practice Exercises" content={parsedContent.practiceExercises} />
                )}
              </div>
            </div>
          ) : null}
        </div>

        {/* Resizer */}
        {!isFullscreen && type === 'challenge' && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
            className={`w-[1px] cursor-col-resize transition-colors flex-shrink-0 relative z-10 group ${
              isResizing ? 'bg-blue-500' : 'bg-[#0E1B2E]/10 hover:bg-blue-500'
            }`}
          >
            {/* Grip handle visual */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-8 bg-white border border-[#0E1B2E]/10 rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <div className="w-0.5 h-4 bg-[#0E1B2E]/20 rounded-full" />
            </div>
          </div>
        )}
        {!isFullscreen && type === 'tutorial' && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
            className="w-[1px] cursor-col-resize hover:bg-blue-500 transition-colors flex-shrink-0 relative z-10 group bg-slate-200"
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-8 bg-white border border-slate-300 rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <div className="w-0.5 h-4 bg-slate-400 rounded-full" />
            </div>
          </div>
        )}

        {/* Right Panel - Code Steps & Explanation (for tutorials) or Code Editor (for challenges) */}
        <div
          className={`flex flex-col flex-1 overflow-hidden ${
            type === 'challenge' ? 'bg-[#1e1e1e]' : 'bg-white'
          } ${isFullscreen ? 'w-full' : ''}`}
          style={!isFullscreen ? { width: `${100 - leftPanelWidth}%` } : {}}
        >
          {type === 'tutorial' && parsedContent ? (
            <div className="flex-1 overflow-y-auto px-8 py-6 bg-slate-50/50">
              <div className="max-w-4xl mx-auto space-y-8">
                {/* Right side content for tutorials: Steps and Code Explanation */}
                {parsedContent.steps.length > 0 && (
                  <div className="py-2">
                    <StepByStepSection steps={parsedContent.steps} />
                  </div>
                )}
                {parsedContent.codeExplanation && (
                  <ContentSection title="Code Explanation" content={parsedContent.codeExplanation} />
                )}
              </div>
            </div>
          ) : type === 'challenge' ? (
            <div className="h-full">
              <CodeEditor
                prData={challengePrData || undefined}
                isFullscreen={isFullscreen}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onEvaluationComplete={handleEvaluationComplete}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              <p>No code changes available</p>
            </div>
          )}
        </div>
      </div>

      {showEvaluationModal && (
        <EvaluationModal
          evaluationData={evaluationData}
          onClose={() => setShowEvaluationModal(false)}
        />
      )}
    </div>
  );
}

