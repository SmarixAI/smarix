'use client';

import { useState, useEffect } from 'react';
import type { PRTutorial } from '../../../../../../types/onboarding';
import { parseTutorialContent } from '../../../utils/BugFix/contentParser';
import ContentSection from '../../../utils/BugFix/ContentSection';
import StepByStepSection from '../../../utils/BugFix/StepByStepSection';

interface TutorialContentProps {
  darkMode: boolean;
  tutorial: PRTutorial;
}

export default function TutorialContent({ darkMode, tutorial }: TutorialContentProps) {
  const [parsedContent, setParsedContent] = useState<any>(null);

  useEffect(() => {
    const content = parseTutorialContent(tutorial.raw_response);
    setParsedContent(content);
  }, [tutorial]);

  if (!parsedContent) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Overview */}
      {parsedContent.overview && (
        <ContentSection
          title="📚 Overview" 
          content={parsedContent.overview}
          color="blue"
          darkMode={darkMode}
        />
      )}

      {/* Problem Context */}
      {parsedContent.problemContext && (
        <ContentSection 
          title="🔍 Problem Context" 
          content={parsedContent.problemContext}
          color="purple"
          darkMode={darkMode}
        />
      )}

      {/* Step-by-Step Implementation */}
      {parsedContent.steps.length > 0 && (
        <StepByStepSection steps={parsedContent.steps} darkMode={darkMode} />
      )}

      {/* Code Explanation */}
      {parsedContent.codeExplanation && (
        <ContentSection 
          title="💡 Code Explanation" 
          content={parsedContent.codeExplanation}
          color="green"
          darkMode={darkMode}
        />
      )}

      {/* Testing */}
      {parsedContent.testing && (
        <ContentSection 
          title="🧪 Testing" 
          content={parsedContent.testing}
          color="orange"
          darkMode={darkMode}
        />
      )}

      {/* Key Takeaways */}
      {parsedContent.keyTakeaways && (
        <ContentSection 
          title="⭐ Key Takeaways" 
          content={parsedContent.keyTakeaways}
          color="pink"
          darkMode={darkMode}
        />
      )}

      {/* Practice Exercises */}
      {parsedContent.practiceExercises && (
        <ContentSection 
          title="💪 Practice Exercises" 
          content={parsedContent.practiceExercises}
          color="indigo"
          darkMode={darkMode}
        />
      )}
    </div>
  );
}
