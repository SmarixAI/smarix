'use client';

import type { CodingQuestion } from '../../../../../../types/onboarding';

interface ChallengeCardProps {
  challenge: CodingQuestion;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

export default function ChallengeCard({ challenge, index, isSelected, onSelect }: ChallengeCardProps) {
  const difficultyMatch = challenge.raw_response.match(/Difficulty:\s*(\w+)/i);
  const timeMatch = challenge.raw_response.match(/Estimated time:\s*([^\n]+)/i);
  
  const difficulty = difficultyMatch?.[1] || 'Medium';
  const time = timeMatch?.[1] || '30-60 min';

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border px-4 py-2.5 text-left transition-all hover:shadow-sm ${
        isSelected
          ? 'border-gray-800 bg-gray-100'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="font-semibold text-sm text-gray-900">
          Challenge {challenge.question_number}
        </h4>
        <span className="px-2 py-0.5 rounded text-[10px] font-semibold border border-gray-300 bg-gray-50 text-gray-700">
          {difficulty}
        </span>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-700">
            {challenge.category}
          </span>
          <span className="text-[10px] flex items-center text-gray-600">
            ⏱️ {time}
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-700">
          Solve
        </span>
      </div>
    </button>
  );
}
