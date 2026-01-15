'use client';

import type { CodingQuestion } from '../../../../../../types/onboarding';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { Clock, Trophy, ArrowRight } from 'lucide-react';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

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

  const getDifficultyColor = (diff: string) => {
    const lower = diff.toLowerCase();
    if (lower.includes('easy')) return 'bg-emerald-50 text-emerald-700 border-emerald-100';
    if (lower.includes('hard')) return 'bg-rose-50 text-rose-700 border-rose-100';
    return 'bg-amber-50 text-amber-700 border-amber-100';
  };

  const getCategoryColor = (category: string) => {
    // Using palette safe colors
    const colors = ['#0E1B2E', '#3B82F6', '#8B5CF6', '#10B981', '#F59E0B'];
    return colors[index % colors.length];
  };

  const categoryColor = getCategoryColor(challenge.category);

  return (
    <button
      onClick={onSelect}
      className={`group w-full rounded-xl border-2 px-6 py-5 text-left transition-all duration-300 relative overflow-hidden flex flex-col h-full ${
        isSelected
          ? 'border-[#0E1B2E] bg-white shadow-xl shadow-[#0E1B2E]/5 ring-1 ring-[#0E1B2E]/5 scale-[1.02] z-10'
          : 'border-[#0E1B2E]/5 bg-white hover:border-[#0E1B2E]/20 hover:shadow-lg hover:shadow-[#0E1B2E]/5 hover:-translate-y-1'
      }`}
    >
      {isSelected && (
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-[#0E1B2E]/5 to-transparent -mr-10 -mt-10 rounded-full blur-2xl" />
      )}
      
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-300 shadow-sm ${
              isSelected 
                ? 'bg-[#0E1B2E] text-white' 
                : 'bg-[#0E1B2E]/5 text-[#0E1B2E]/70 group-hover:bg-[#0E1B2E] group-hover:text-white'
            }`}>
              <span className={`${jetbrainsMono.className} text-sm font-bold`}>
                {challenge.question_number}
              </span>
            </div>
            <span className={`${jetbrainsMono.className} text-xs font-bold uppercase tracking-wider text-[#0E1B2E]/40`}>
              Challenge
            </span>
          </div>
          <span className={`${inter.className} px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border ${getDifficultyColor(difficulty)}`}>
            {difficulty}
          </span>
        </div>
        
        {/* Content */}
        <div className="flex-1">
          <div className="flex flex-wrap gap-2 mb-3">
            <span 
              className={`${jetbrainsMono.className} px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border bg-opacity-10`}
              style={{
                backgroundColor: `${categoryColor}10`,
                color: categoryColor,
                borderColor: `${categoryColor}20`
              }}
            >
              {challenge.category}
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-[#0E1B2E]/60 mb-4 font-medium">
            <Clock className="w-3.5 h-3.5" />
            <span>{time}</span>
          </div>
        </div>
        
        {/* Footer Action */}
        <div className={`pt-4 border-t border-[#0E1B2E]/5 mt-auto flex items-center justify-between transition-colors duration-300 ${
           isSelected ? 'border-[#0E1B2E]/10' : ''
        }`}>
          <span className={`${inter.className} text-xs font-bold text-[#0E1B2E]/40 group-hover:text-[#0E1B2E] transition-colors`}>
            Start Debugging
          </span>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 ${
            isSelected ? 'bg-[#0E1B2E] text-white' : 'bg-[#0E1B2E]/5 text-[#0E1B2E] group-hover:bg-[#0E1B2E] group-hover:text-white'
          }`}>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>
      </div>
    </button>
  );
}