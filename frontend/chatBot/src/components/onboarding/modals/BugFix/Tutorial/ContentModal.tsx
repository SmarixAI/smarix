'use client';

import { useState, useEffect } from 'react';
import type { PRTutorialsResponse, PRTutorial } from '../../../../../../types/onboarding';
import TutorialCard from '../../../cards/BugFix/Tutorial/ModuleCard';
import TutorialContent from '../../../cards/BugFix/Tutorial/ModuleContent';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { Sparkles } from 'lucide-react';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'] });

interface TutorialSectionProps {
  data: PRTutorialsResponse;
}

export default function TutorialSection({ data }: TutorialSectionProps) {
  const [selectedTutorial, setSelectedTutorial] = useState<PRTutorial | null>(null);

  // Auto-select first tutorial
  useEffect(() => {
    if (data && data.tutorials.length > 0 && !selectedTutorial) {
      setSelectedTutorial(data.tutorials[0]);
    }
  }, [data, selectedTutorial]);

  return (
    <div className="animate-in fade-in duration-500">
      <div className="mb-8 flex items-end justify-between border-b border-[#0E1B2E]/5 pb-6">
        <div>
          <h3 className={`${inter.className} text-xl font-bold tracking-tight mb-2 text-[#0E1B2E] flex items-center gap-2`}>
            <Sparkles className="w-5 h-5 text-amber-500" />
            Tutorial Modules
          </h3>
          <p className={`${inter.className} text-[15px] text-[#0E1B2E]/60 max-w-2xl leading-relaxed`}>
            Select a module below to view the step-by-step breakdown of the bug fix.
          </p>
        </div>
        <div className={`${jetbrainsMono.className} text-xs font-medium text-[#0E1B2E]/40 bg-[#0E1B2E]/5 px-3 py-1.5 rounded-lg`}>
          {data.tutorials.length} Available
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        {data.tutorials.map((tutorial, idx) => (
          <TutorialCard
            key={tutorial.tutorial_number}
            tutorial={tutorial}
            index={idx}
            isSelected={selectedTutorial?.tutorial_number === tutorial.tutorial_number}
            onSelect={() => setSelectedTutorial(tutorial)}
          />
        ))}
      </div>

      <div className="min-h-[400px]">
        {selectedTutorial ? (
          <TutorialContent tutorial={selectedTutorial} />
        ) : (
          <div className="h-64 rounded-2xl border-2 border-dashed border-[#0E1B2E]/10 flex items-center justify-center">
            <p className={`${inter.className} text-[#0E1B2E]/40 text-sm`}>Select a tutorial to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}