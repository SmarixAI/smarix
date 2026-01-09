'use client';

import type { PRTutorial } from '../../../../../../types/onboarding';

interface TutorialCardProps {
  tutorial: PRTutorial;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

export default function TutorialCard({ tutorial, index, isSelected, onSelect }: TutorialCardProps) {
  const getDifficultyColor = (difficulty: string) => {
    const lower = difficulty.toLowerCase();
    if (lower.includes('easy')) return 'bg-green-100 text-green-700 border-green-200';
    if (lower.includes('hard')) return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-amber-100 text-amber-700 border-amber-200';
  };

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border px-5 py-4 text-left transition-all group relative overflow-hidden ${
        isSelected
          ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 shadow-md'
          : 'border-gray-200 bg-white hover:border-[#8B5CF6]/40 hover:shadow-md'
      }`}
    >
      {/* Subtle accent background on hover */}
      {!isSelected && (
        <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-5 transition-opacity duration-200 pointer-events-none bg-[#8B5CF6]" />
      )}
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isSelected ? 'bg-[#8B5CF6]' : 'bg-[#8B5CF6]/10'
            }`}>
              <span className={`text-sm font-bold ${
                isSelected ? 'text-white' : 'text-[#8B5CF6]'
              }`}>
                {tutorial.tutorial_number}
              </span>
            </div>
            <h4 className={`font-bold text-sm ${
              isSelected ? 'text-[#0E1B2E]' : 'text-[#0E1B2E]'
            }`}>
              Tutorial {tutorial.tutorial_number}
            </h4>
          </div>
          <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${getDifficultyColor(tutorial.difficulty)}`}>
            {tutorial.difficulty}
          </span>
        </div>
        
        <p className="text-sm text-[#0E1B2E]/70 line-clamp-2 leading-relaxed">
          {tutorial.pr_title}
        </p>
      </div>
    </button>
  );
}
