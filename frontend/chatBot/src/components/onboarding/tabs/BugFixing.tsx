'use client';

import { useState, useEffect } from 'react';
import { Bug, Loader2, BookOpen, Code2, Sparkles } from 'lucide-react';
import type { PRTutorialsResponse, CodingQuestionsResponse } from '../../../../types/onboarding';
import TutorialSection from '../modals/BugFix/Tutorial/ContentModal';
import ChallengeSection from '../modals/BugFix/Challenge/ContentModal';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

interface BugFixingProps {
  employeeId?: string | null;
  onboardingData?: any;
  activeRepos?: string[];
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

export default function BugFixing({ employeeId, onboardingData, activeRepos = [], onUpdateProgress }: BugFixingProps) {
  const [tutorials, setTutorials] = useState<PRTutorialsResponse | null>(null);
  const [challenges, setChallenges] = useState<CodingQuestionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'tutorials' | 'challenges'>('tutorials');

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      // Use the first active repo if available
      const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
      const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';
      
      try {
        const [tutorialsRes, challengesRes] = await Promise.all([
          fetch(`/api/onboarding/bugFix/tutorials${repoParam}`),
          fetch(`/api/onboarding/bugFix/challenges${repoParam}`),
        ]);

        if (tutorialsRes.ok) {
          const tutData = await tutorialsRes.json();
          setTutorials(tutData);
        }

        if (challengesRes.ok) {
          const chalData = await challengesRes.json();
          setChallenges(chalData);
        }
      } catch (error) {
        console.error('Error fetching bug fix data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className={`${inter.className} text-sm text-slate-600 font-medium`}>Loading bug fix modules...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full relative space-y-6">
      {/* Header Section */}
      <div className="rounded-2xl border-2 border-slate-200 p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white/70 backdrop-blur-sm shadow-md shadow-slate-200/40">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0E1B2E] to-blue-900 flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Bug className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className={`${inter.className} text-2xl font-bold tracking-tight text-[#0E1B2E] mb-1.5`}>
              Bug Fix Training
            </h2>
            <p className={`${inter.className} text-[15px] text-slate-600 leading-relaxed max-w-xl`}>
              Master debugging with hands-on tutorials and real-world challenges designed to improve your problem-solving skills.
            </p>
          </div>
        </div>

        {/* Tabs - Styled as a Segmented Control */}
        <div className="flex items-center p-1.5 bg-slate-100/80 rounded-xl border border-slate-200">
          <button
            onClick={() => setActiveTab('tutorials')}
            className={`${inter.className} flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === 'tutorials'
                ? 'bg-white text-[#0E1B2E] shadow-sm ring-1 ring-black/5'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
            }`}
          >
            <BookOpen className={`w-4 h-4 ${activeTab === 'tutorials' ? 'text-blue-600' : ''}`} />
            <span>Tutorial Bugs</span>
            <span className={`${jetbrainsMono.className} text-xs ml-1.5 px-2 py-0.5 rounded-md ${
              activeTab === 'tutorials'
                ? 'bg-[#0E1B2E] text-white'
                : 'bg-slate-200 text-slate-600'
            }`}>
              {tutorials?.tutorials.length || 0}
            </span>
          </button>
          
          <button
            onClick={() => setActiveTab('challenges')}
            className={`${inter.className} flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === 'challenges'
                ? 'bg-white text-[#0E1B2E] shadow-sm ring-1 ring-black/5'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
            }`}
          >
            <Code2 className={`w-4 h-4 ${activeTab === 'challenges' ? 'text-amber-600' : ''}`} />
            <span>Challenge Bugs</span>
            <span className={`${jetbrainsMono.className} text-xs ml-1.5 px-2 py-0.5 rounded-md ${
              activeTab === 'challenges'
                ? 'bg-[#0E1B2E] text-white'
                : 'bg-slate-200 text-slate-600'
            }`}>
              {challenges?.questions.length || 0}
            </span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        {activeTab === 'tutorials' && tutorials && (
          <TutorialSection data={tutorials} />
        )}
        
        {activeTab === 'challenges' && challenges && (
          <ChallengeSection data={challenges} activeRepos={activeRepos} />
        )}
      </div>
    </div>
  );
}