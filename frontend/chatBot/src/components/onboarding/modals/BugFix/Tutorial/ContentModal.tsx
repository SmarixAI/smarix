'use client';

import { useState } from 'react';
import type { PRTutorialsResponse, PRTutorial } from '../../../../../../types/onboarding';
import TutorialCard from '../../../cards/BugFix/Tutorial/ModuleCard';
import TutorialContent from '../../../cards/BugFix/Tutorial/ModuleContent';

interface TutorialSectionProps {
  data: PRTutorialsResponse;
}

export default function TutorialSection({ data }: TutorialSectionProps) {
  const [selectedTutorial, setSelectedTutorial] = useState<PRTutorial | null>(null);

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-bold tracking-tight mb-2 text-[#0E1B2E]">
          Tutorial Bugs
        </h3>
        <p className="text-sm text-[#0E1B2E]/60">
          Learn debugging techniques through guided tutorials
        </p>
      </div>
      
      <div className="grid grid-cols-3 gap-5 mb-6">
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

      {selectedTutorial && (
        <TutorialContent tutorial={selectedTutorial} />
      )}
    </div>
  );
}
