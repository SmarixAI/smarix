'use client';

import { useState } from 'react';
import type { CodingQuestionsResponse, CodingQuestion } from '../../../../../../types/onboarding';
import ChallengeCard from '../../../cards/BugFix/Challenge/ModuleCard';
import ChallengeContent from '../../../cards/BugFix/Challenge/ModuleContent';

interface ChallengeSectionProps {
  data: CodingQuestionsResponse;
  activeRepos?: string[];
}

export default function ChallengeSection({ data, activeRepos = [] }: ChallengeSectionProps) {
  const [selectedChallenge, setSelectedChallenge] = useState<CodingQuestion | null>(null);

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-bold tracking-tight mb-2 text-[#0E1B2E]">
          Challenge Bugs
        </h3>
        <p className="text-sm text-[#0E1B2E]/60">
          Test your skills with real-world debugging challenges
        </p>
      </div>
      
      <div className="mb-6 overflow-x-auto">
        <div className="flex gap-4 pb-2" style={{ minWidth: 'min-content' }}>
          {data.questions.map((question, idx) => (
            <div key={question.question_number} className="flex-shrink-0" style={{ width: '300px' }}>
              <ChallengeCard
                challenge={question}
                index={idx}
                isSelected={selectedChallenge?.question_number === question.question_number}
                onSelect={() => setSelectedChallenge(question)}
              />
            </div>
          ))}
        </div>
      </div>

      {selectedChallenge && (
        <ChallengeContent challenge={selectedChallenge} activeRepos={activeRepos} />
      )}
    </div>
  );
}
