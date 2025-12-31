'use client';

import type { PRTutorial } from '../../../../../../types/onboarding';

interface TutorialCardProps {
  tutorial: PRTutorial;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
  darkMode: boolean;
}

export default function TutorialCard({ tutorial, index, isSelected, onSelect, darkMode }: TutorialCardProps) {
  const getDifficultyColor = (difficulty: string) => {
    if (darkMode) {
      switch (difficulty) {
        case 'Easy':
          return 'bg-green-900/50 text-green-300 border-green-700';
        case 'Medium':
          return 'bg-yellow-900/50 text-yellow-300 border-yellow-700';
        case 'Hard':
          return 'bg-red-900/50 text-red-300 border-red-700';
        default:
          return 'bg-gray-800 text-gray-300 border-gray-700';
      }
    } else {
      switch (difficulty) {
        case 'Easy':
          return 'bg-green-100 text-green-700 border-green-300';
        case 'Medium':
          return 'bg-yellow-100 text-yellow-700 border-yellow-300';
        case 'Hard':
          return 'bg-red-100 text-red-700 border-red-300';
        default:
          return 'bg-gray-100 text-gray-700 border-gray-300';
      }
    }
  };

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border-2 px-4 py-2.5 text-left transition-all hover:shadow-md ${
        isSelected
          ? darkMode
            ? 'border-blue-500 bg-gradient-to-br from-blue-900/50 to-indigo-900/50 shadow-lg'
            : 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg'
          : darkMode
          ? 'border-gray-700 bg-gray-800 hover:border-gray-600'
          : 'border-slate-200 bg-white hover:border-slate-300'
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <h4 className={`font-bold text-sm ${darkMode ? 'text-white' : 'text-slate-900'}`}>
            Tutorial {tutorial.tutorial_number}
          </h4>
          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
            darkMode ? 'bg-purple-900/50 text-purple-300' : 'bg-purple-100 text-purple-700'
          }`}>
            Tutorial
          </span>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getDifficultyColor(tutorial.difficulty)}`}>
          {tutorial.difficulty}
        </span>
      </div>
      
      <p className={`text-xs line-clamp-1 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
        {tutorial.pr_title}
      </p>
    </button>
  );
}
