'use client';

import { useState, useEffect } from 'react';
import type { PRTutorial } from '../../../../../../types/onboarding';
import { parseTutorialContent } from '../../../utils/BugFix/contentParser';
import ContentSection from '../../../utils/BugFix/ContentSection';
import StepByStepSection from '../../../utils/BugFix/StepByStepSection';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { FileText, GitPullRequest } from 'lucide-react';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'] });

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
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Document Header */}
      <div className="bg-white rounded-t-2xl border-2 border-[#0E1B2E]/10 border-b-0 p-8">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#0E1B2E] to-blue-900 flex items-center justify-center shadow-lg shadow-[#0E1B2E]/10 flex-shrink-0">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className={`${inter.className} text-2xl font-bold text-[#0E1B2E] mb-2`}>
              {tutorial.pr_title}
            </h2>
            <div className="flex items-center gap-3">
               <span className={`${jetbrainsMono.className} text-xs font-medium px-2.5 py-1 rounded bg-[#0E1B2E]/5 text-[#0E1B2E]/70`}>
                 ID: #{tutorial.tutorial_number}
               </span>
               <div className="flex items-center gap-1.5 text-xs text-[#0E1B2E]/50 font-medium">
                  <GitPullRequest className="w-3.5 h-3.5" />
                  <span>Pull Request Analysis</span>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="bg-white/50 backdrop-blur-sm rounded-b-2xl border-2 border-[#0E1B2E]/10 p-6 md:p-8 space-y-8">
        
        {parsedContent.overview && (
          <ContentSection
            title="Overview" 
            content={parsedContent.overview}
          />
        )}

        {parsedContent.problemContext && (
          <ContentSection 
            title="Problem Context" 
            content={parsedContent.problemContext}
          />
        )}

        {/* The step-by-step section usually contains code blocks, ensuring those look good is handled by that component, 
            but this wrapper provides the whitespace breathing room */}
        {parsedContent.steps.length > 0 && (
          <div className="py-2">
            <StepByStepSection steps={parsedContent.steps} />
          </div>
        )}

        {parsedContent.codeExplanation && (
          <ContentSection 
            title="Code Explanation" 
            content={parsedContent.codeExplanation}
          />
        )}

        {parsedContent.testing && (
          <ContentSection 
            title="Testing Strategy" 
            content={parsedContent.testing}
          />
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {parsedContent.keyTakeaways && (
            <div className="h-full">
              <ContentSection 
                title="Key Takeaways" 
                content={parsedContent.keyTakeaways}
              />
            </div>
          )}

          {parsedContent.practiceExercises && (
            <div className="h-full">
              <ContentSection 
                title="Practice Exercises" 
                content={parsedContent.practiceExercises}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}