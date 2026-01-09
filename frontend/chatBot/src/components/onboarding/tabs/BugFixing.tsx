'use client';

import { useState, useEffect } from 'react';
import { Bug, Loader2 } from 'lucide-react';
import type { PRTutorialsResponse, CodingQuestionsResponse } from '../../../../types/onboarding';
import TutorialSection from '../modals/BugFix/Tutorial/ContentModal';
import ChallengeSection from '../modals/BugFix/Challenge/ContentModal';

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
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-16 h-16 animate-spin text-[#0E1B2E]/60" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-[#0E1B2E]/5 to-[#0E1B2E]/10 rounded-lg p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[#8B5CF6] flex items-center justify-center">
              <Bug className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[#0E1B2E] mb-1">
                Bug Fix Training
              </h2>
              <p className="text-sm text-[#0E1B2E]/60">
                Master debugging with hands-on tutorials and real-world challenges
              </p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('tutorials')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'tutorials'
                  ? 'bg-[#0E1B2E] text-white shadow-sm'
                  : 'bg-white text-[#0E1B2E]/70 hover:bg-[#0E1B2E]/5 border border-gray-200'
              }`}
            >
              <span>Tutorial Bugs</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                activeTab === 'tutorials'
                  ? 'bg-white/20 text-white'
                  : 'bg-[#0E1B2E]/5 text-[#0E1B2E]/70'
              }`}>
                {tutorials?.tutorials.length || 0}
              </span>
            </button>
            
            <button
              onClick={() => setActiveTab('challenges')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'challenges'
                  ? 'bg-[#0E1B2E] text-white shadow-sm'
                  : 'bg-white text-[#0E1B2E]/70 hover:bg-[#0E1B2E]/5 border border-gray-200'
              }`}
            >
              <span>Challenge Bugs</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                activeTab === 'challenges'
                  ? 'bg-white/20 text-white'
                  : 'bg-[#0E1B2E]/5 text-[#0E1B2E]/70'
              }`}>
                {challenges?.questions.length || 0}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'tutorials' && tutorials && (
        <TutorialSection data={tutorials} />
      )}
      
      {activeTab === 'challenges' && challenges && (
        <ChallengeSection data={challenges} activeRepos={activeRepos} />
      )}
    </div>
  );
}
