'use client';

import type { CodingQuestion } from '../../../../../../types/onboarding';

interface ChallengeCardProps {
  challenge: CodingQuestion;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
  darkMode: boolean;
}

const icons = ['🎨', '✨', '🧪', '🔧'];

export default function ChallengeCard({ challenge, index, isSelected, onSelect, darkMode }: ChallengeCardProps) {
  const difficultyMatch = challenge.raw_response.match(/Difficulty:\s*(\w+)/i);
  const timeMatch = challenge.raw_response.match(/Estimated time:\s*([^\n]+)/i);
  
  const difficulty = difficultyMatch?.[1] || 'Medium';
  const time = timeMatch?.[1] || '30-60 min';

  const getDifficultyColor = (diff: string) => {
    if (darkMode) {
      switch (diff) {
        case 'Easy':
          return 'bg-green-900/50 text-green-300 border-green-700';
        case 'Medium':
        case 'Intermediate':
          return 'bg-yellow-900/50 text-yellow-300 border-yellow-700';
        case 'Hard':
          return 'bg-red-900/50 text-red-300 border-red-700';
        default:
          return 'bg-gray-800 text-gray-300 border-gray-700';
      }
    } else {
      switch (diff) {
        case 'Easy':
          return 'bg-green-100 text-green-700 border-green-300';
        case 'Medium':
        case 'Intermediate':
          return 'bg-yellow-100 text-yellow-700 border-yellow-300';
        case 'Hard':
          return 'bg-red-100 text-red-700 border-red-300';
        default:
          return 'bg-gray-100 text-gray-700 border-gray-300';
      }
    }
  };

  const getCategoryColor = (category: string) => {
    if (darkMode) {
      switch (category) {
        case 'UI':
          return 'bg-blue-900/50 text-blue-300';
        case 'Feature':
          return 'bg-purple-900/50 text-purple-300';
        case 'Test':
          return 'bg-orange-900/50 text-orange-300';
        default:
          return 'bg-gray-800 text-gray-300';
      }
    } else {
      switch (category) {
        case 'UI':
          return 'bg-blue-100 text-blue-700';
        case 'Feature':
          return 'bg-purple-100 text-purple-700';
        case 'Test':
          return 'bg-orange-100 text-orange-700';
        default:
          return 'bg-slate-100 text-slate-700';
      }
    }
  };

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border-2 px-4 py-2.5 text-left transition-all hover:shadow-md ${
        isSelected
          ? darkMode
            ? 'border-green-500 bg-gradient-to-br from-green-900/50 to-emerald-900/50 shadow-lg'
            : 'border-green-500 bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg'
          : darkMode
          ? 'border-gray-700 bg-gray-800 hover:border-gray-600'
          : 'border-slate-200 bg-white hover:border-slate-300'
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <h4 className={`font-bold text-sm ${darkMode ? 'text-white' : 'text-slate-900'}`}>
          Challenge {challenge.question_number}
        </h4>
        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getDifficultyColor(difficulty)}`}>
          {difficulty}
        </span>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getCategoryColor(challenge.category)}`}>
            {challenge.category}
          </span>
          <span className={`text-[10px] flex items-center ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
            ⏱️ {time}
          </span>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
          darkMode ? 'bg-red-900/50 text-red-300' : 'bg-red-100 text-red-700'
        }`}>
          🎯 Solve
        </span>
      </div>
    </button>
  );
}
