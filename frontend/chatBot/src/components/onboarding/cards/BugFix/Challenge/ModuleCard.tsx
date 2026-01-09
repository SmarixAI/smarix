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

  const getDifficultyColor = (difficulty: string) => {
    const lower = difficulty.toLowerCase();
    if (lower.includes('easy')) return 'bg-green-100 text-green-700 border-green-200';
    if (lower.includes('hard')) return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-amber-100 text-amber-700 border-amber-200';
  };

  const getCategoryColor = (category: string) => {
    // Using landing page colors
    const colors = ['#3B82F6', '#6366F1', '#10B981', '#06B6D4', '#8B5CF6'];
    const color = colors[index % colors.length];
    return color;
  };

  const categoryColor = getCategoryColor(challenge.category);

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border px-5 py-4 text-left transition-all group relative overflow-hidden ${
        isSelected
          ? 'border-[#10B981] bg-[#10B981]/5 shadow-md'
          : 'border-gray-200 bg-white hover:border-[#10B981]/40 hover:shadow-md'
      }`}
    >
      {/* Subtle accent background on hover */}
      {!isSelected && (
        <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-5 transition-opacity duration-200 pointer-events-none bg-[#10B981]" />
      )}
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isSelected ? 'bg-[#10B981]' : 'bg-[#10B981]/10'
            }`}>
              <span className={`text-sm font-bold ${
                isSelected ? 'text-white' : 'text-[#10B981]'
              }`}>
                {challenge.question_number}
              </span>
            </div>
            <h4 className={`font-bold text-sm ${
              isSelected ? 'text-[#0E1B2E]' : 'text-[#0E1B2E]'
            }`}>
              Challenge {challenge.question_number}
            </h4>
          </div>
          <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${getDifficultyColor(difficulty)}`}>
            {difficulty}
          </span>
        </div>
        
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span 
              className="px-2.5 py-1 rounded-md text-xs font-medium border"
              style={{
                backgroundColor: `${categoryColor}15`,
                color: categoryColor,
                borderColor: `${categoryColor}30`
              }}
            >
              {challenge.category}
            </span>
            <span className="text-xs flex items-center text-[#0E1B2E]/60">
              ⏱️ {time}
            </span>
          </div>
        </div>
        
        <div className="mt-3 pt-3 border-t border-gray-100">
          <span className="text-xs font-semibold text-[#0E1B2E]/70">
            Start Challenge →
          </span>
        </div>
      </div>
    </button>
  );
}
