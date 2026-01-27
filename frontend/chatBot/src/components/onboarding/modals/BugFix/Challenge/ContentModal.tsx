'use client';

import { useState } from 'react';
import type { CodingQuestionsResponse, CodingQuestion } from '../../../../../../types/onboarding';
import ChallengeCard from '../../../cards/BugFix/Challenge/ModuleCard';
import ChallengeContent from '../../../cards/BugFix/Challenge/ModuleContent';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { Code2 } from 'lucide-react';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'] });

interface ChallengeSectionProps {
  data: CodingQuestionsResponse;
  activeRepos?: string[];
}

export default function ChallengeSection({ data, activeRepos = [] }: ChallengeSectionProps) {
  const [selectedChallenge, setSelectedChallenge] = useState<CodingQuestion | null>(null);

  return (
    <div className="animate-in fade-in duration-500">
      <div className="mb-8 flex items-end justify-between border-b border-[#0E1B2E]/5 pb-6">
        <div>
          <h3 className={`${inter.className} text-xl font-bold tracking-tight mb-2 text-[#0E1B2E] flex items-center gap-2`}>
            <Code2 className="w-5 h-5 text-blue-600" />
            Challenge Bugs
          </h3>
          <p className={`${inter.className} text-[15px] text-[#0E1B2E]/60 leading-relaxed`}>
            Test your debugging skills with these real-world scenarios. Each challenge simulates a common issue found in production.
          </p>
        </div>
        <div className={`${jetbrainsMono.className} text-xs font-medium text-[#0E1B2E]/40 bg-[#0E1B2E]/5 px-3 py-1.5 rounded-lg`}>
          {data.questions.length} Challenges
        </div>
      </div>
      
      <div className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.questions.map((question, idx) => (
            <ChallengeCard
              key={question.question_number}
              challenge={question}
              index={idx}
              isSelected={selectedChallenge?.question_number === question.question_number}
              onSelect={() => setSelectedChallenge(question)}
            />
          ))}
        </div>
      </div>

      <div className="min-h-[400px]">
        {selectedChallenge ? (
          <ChallengeContent challenge={selectedChallenge} activeRepos={activeRepos} />
        ) : (
          <div className="h-64 rounded-2xl border-2 border-dashed border-[#0E1B2E]/10 flex items-center justify-center bg-[#0E1B2E]/[0.02]">
            <p className={`${inter.className} text-[#0E1B2E]/40 text-sm flex items-center gap-2`}>
              <Code2 className="w-4 h-4" />
              Select a challenge to start debugging
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
