interface ParsedContent {
  overview: string;
  problemContext: string;
  steps: { title: string; content: string }[];
  codeExplanation: string;
  testing: string;
  keyTakeaways: string;
  practiceExercises: string;
}

export function parseTutorialContent(rawContent: string): ParsedContent {
  const sections = rawContent.split(/\n## /);
  
  const parsed: ParsedContent = {
    overview: '',
    problemContext: '',
    steps: [],
    codeExplanation: '',
    testing: '',
    keyTakeaways: '',
    practiceExercises: '',
  };

  sections.forEach((section) => {
    const lines = section.split('\n');
    const title = lines[0].replace(/^#+\s*/, '').replace(/^\d+\.\s*/, '').trim().toLowerCase();
    const sectionContent = lines.slice(1).join('\n').trim();

    if (title.includes('overview')) {
      parsed.overview = sectionContent;
    } else if (title.includes('problem context') || title.includes('problem statement')) {
      parsed.problemContext = sectionContent;
    } else if (title.includes('step-by-step') || title.includes('implementation')) {
      // Parse individual steps
      const stepSections = sectionContent.split(/\n### Step \d+:/);
      stepSections.forEach((step, idx) => {
        if (step.trim() && idx > 0) {
          const stepLines = step.split('\n');
          const stepTitle = stepLines[0]?.trim() || `Step ${idx}`;
          const stepContent = stepLines.slice(1).join('\n').trim();
          parsed.steps.push({ title: stepTitle, content: stepContent });
        }
      });
      
      // Alternative parsing if no steps found
      if (parsed.steps.length === 0) {
        const altStepSections = sectionContent.split(/\n### /);
        altStepSections.forEach((step, idx) => {
          if (step.trim() && idx > 0) {
            const stepLines = step.split('\n');
            const stepTitle = stepLines[0]?.replace(/^Step \d+:\s*/, '').trim() || `Step ${idx}`;
            const stepContent = stepLines.slice(1).join('\n').trim();
            if (stepContent) {
              parsed.steps.push({ title: stepTitle, content: stepContent });
            }
          }
        });
      }
    } else if (title.includes('code explanation') || title.includes('explanation')) {
      parsed.codeExplanation = sectionContent;
    } else if (title.includes('testing') || title.includes('test')) {
      parsed.testing = sectionContent;
    } else if (title.includes('key takeaways') || title.includes('takeaway')) {
      parsed.keyTakeaways = sectionContent;
    } else if (title.includes('practice') || title.includes('exercise')) {
      parsed.practiceExercises = sectionContent;
    }
  });

  // Final fallback: if still no steps, try to parse any section with "step" in title
  if (parsed.steps.length === 0) {
    sections.forEach((section) => {
      const lines = section.split('\n');
      const title = lines[0].replace(/^#+\s*/, '').trim();
      if (title.toLowerCase().includes('step')) {
        const content = lines.slice(1).join('\n').trim();
        if (content) {
          parsed.steps.push({ title, content });
        }
      }
    });
  }

  return parsed;
}
