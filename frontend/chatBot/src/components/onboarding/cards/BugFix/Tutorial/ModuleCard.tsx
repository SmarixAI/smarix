'use client';

import type { PRTutorial } from '../../../../../../types/onboarding';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { BookOpen, ArrowRight } from 'lucide-react';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

interface TutorialCardProps {
  tutorial: PRTutorial;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

export default function TutorialCard({ tutorial, index, isSelected, onSelect }: TutorialCardProps) {
  const getDifficultyColor = (difficulty: string) => {
    const lower = difficulty.toLowerCase();
    if (lower.includes('easy')) return 'bg-emerald-50 text-emerald-700 border-emerald-100';
    if (lower.includes('hard')) return 'bg-rose-50 text-rose-700 border-rose-100';
    return 'bg-amber-50 text-amber-700 border-amber-100';
  };

  return (
    <button
      onClick={onSelect}
      className={`group w-full rounded-xl border-2 px-6 py-5 text-left transition-all duration-300 relative overflow-hidden ${
        isSelected
          ? 'border-[#0E1B2E] bg-white shadow-lg shadow-[#0E1B2E]/5 ring-1 ring-[#0E1B2E]/5 scale-[1.02]'
          : 'border-[#0E1B2E]/5 bg-white hover:border-[#0E1B2E]/20 hover:shadow-md hover:-translate-y-1'
      }`}
    >
      {isSelected && (
        <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-[#0E1B2E]/5 to-transparent -mr-8 -mt-8 rounded-full blur-xl" />
      )}
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-300 ${
              isSelected ? 'bg-[#0E1B2E] text-white shadow-md' : 'bg-[#0E1B2E]/5 text-[#0E1B2E]/70 group-hover:bg-[#0E1B2E] group-hover:text-white'
            }`}>
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <span className={`${jetbrainsMono.className} text-[10px] font-bold uppercase tracking-wider text-[#0E1B2E]/40 block mb-0.5`}>
                Module
              </span>
              <span className={`${jetbrainsMono.className} text-sm font-bold text-[#0E1B2E]`}>
                {String(tutorial.tutorial_number).padStart(2, '0')}
              </span>
            </div>
          </div>
          
          <span className={`${inter.className} px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wide border ${getDifficultyColor(tutorial.difficulty)}`}>
            {tutorial.difficulty}
          </span>
        </div>
        
        <h4 className={`${inter.className} font-bold text-[15px] text-[#0E1B2E] mb-2 leading-snug group-hover:text-blue-700 transition-colors`}>
          {tutorial.pr_title}
        </h4>

        <div className={`flex items-center gap-2 text-xs font-medium transition-all duration-300 ${
          isSelected ? 'text-[#0E1B2E] translate-x-1' : 'text-[#0E1B2E]/40 group-hover:text-[#0E1B2E] group-hover:translate-x-1'
        }`}>
          <span>View Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </button>
  );
}