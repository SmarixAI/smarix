'use client';

import { useState } from 'react';
import type { PRTutorialsResponse, PRTutorial } from '../../../../../../types/onboarding';
import TutorialCard from '../../../cards/BugFix/Tutorial/ModuleCard';
import TutorialContent from '../../../cards/BugFix/Tutorial/ModuleContent';

interface TutorialSectionProps {
  darkMode: boolean;
  data: PRTutorialsResponse;
}

export default function TutorialSection({ darkMode, data }: TutorialSectionProps) {
  const [selectedTutorial, setSelectedTutorial] = useState<PRTutorial | null>(null);

  return (
    <div>
      <h3 className={`text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
        Select a Tutorial:
      </h3>
      
      <div className="grid grid-cols-3 gap-4 mb-6">
        {data.tutorials.map((tutorial, idx) => (
          <TutorialCard
            key={tutorial.tutorial_number}
            tutorial={tutorial}
            index={idx}
            isSelected={selectedTutorial?.tutorial_number === tutorial.tutorial_number}
            onSelect={() => setSelectedTutorial(tutorial)}
            darkMode={darkMode}
          />
        ))}
      </div>

      {selectedTutorial && (
        <TutorialContent darkMode={darkMode} tutorial={selectedTutorial} />
      )}
    </div>
  );
}
