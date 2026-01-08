'use client';

import type { PRTutorial } from '../../../../../../types/onboarding';

interface TutorialCardProps {
  tutorial: PRTutorial;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

export default function TutorialCard({ tutorial, index, isSelected, onSelect }: TutorialCardProps) {
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
        <div className="flex items-center gap-2">
          <h4 className="font-semibold text-sm text-gray-900">
            Tutorial {tutorial.tutorial_number}
          </h4>
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-700">
            Tutorial
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-semibold border border-gray-300 bg-gray-50 text-gray-700">
          {tutorial.difficulty}
        </span>
      </div>
      
      <p className="text-xs line-clamp-1 text-gray-600">
        {tutorial.pr_title}
      </p>
    </button>
  );
}
