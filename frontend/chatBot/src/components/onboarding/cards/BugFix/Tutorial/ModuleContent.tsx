'use client';

import { useState, useEffect } from 'react';
import type { PRTutorial } from '../../../../../../types/onboarding';
import { parseTutorialContent } from '../../../utils/BugFix/contentParser';
import ContentSection from '../../../utils/BugFix/ContentSection';
import StepByStepSection from '../../../utils/BugFix/StepByStepSection';

interface TutorialContentProps {
  tutorial: PRTutorial;
}

export default function TutorialContent({ tutorial }: TutorialContentProps) {
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
          title="Overview" 
          content={parsedContent.overview}
        />
      )}

      {/* Problem Context */}
      {parsedContent.problemContext && (
        <ContentSection 
          title="Problem Context" 
          content={parsedContent.problemContext}
        />
      )}

      {/* Step-by-Step Implementation */}
      {parsedContent.steps.length > 0 && (
        <StepByStepSection steps={parsedContent.steps} />
      )}

      {/* Code Explanation */}
      {parsedContent.codeExplanation && (
        <ContentSection 
          title="Code Explanation" 
          content={parsedContent.codeExplanation}
        />
      )}

      {/* Testing */}
      {parsedContent.testing && (
        <ContentSection 
          title="Testing" 
          content={parsedContent.testing}
        />
      )}

      {/* Key Takeaways */}
      {parsedContent.keyTakeaways && (
        <ContentSection 
          title="Key Takeaways" 
          content={parsedContent.keyTakeaways}
        />
      )}

      {/* Practice Exercises */}
      {parsedContent.practiceExercises && (
        <ContentSection 
          title="Practice Exercises" 
          content={parsedContent.practiceExercises}
        />
      )}
    </div>
  );
}
