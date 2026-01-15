import { ReactNode } from 'react';

export interface Module {
  id: string;
  title: string;
  description: string;
  duration: string;
  icon: ReactNode;
  color?: string;
  locked?: boolean;
  dataKey?: string;
  jsonFile?: string;
}

export interface ModuleContent {
  topic?: string;
  content?: string;
  quality?: number;
  type?: 'teaching_content' | 'qna';
  title?: string;
  question?: string;
  questions?: Array<{
    question: string;
    options: Record<string, string>;
    correct_answer: string;
    explanation: string;
    subsection?: string;
  }>;
  options?: Record<string, string>;
  correct_answer?: string;
  explanation?: string;
  sectionKey?: string;
}

export interface ContentSection {
  type: 'text' | 'code' | 'mermaid';
  content: string;
  language?: string;
  index?: number;
}

export interface APIResponse {
  metadata?: {
    generated_at: string;
    repository: string;
    provider: string;
    model: string;
  };
  data: {
    [key: string]: ModuleContent;
  };
}

export interface ModuleSectionResponse {
  moduleId: string;
  jsonFile: string;
  metadata?: {
    generated_at: string;
    repository: string;
    provider: string;
    model: string;
  };
  sections: Array<{
    sectionId: string;
    sectionTitle: string;
    content: ModuleContent;
  }>;
  totalSections: number;
}

export interface AllModulesResponse {
  modules: Array<{
    moduleId: string;
    jsonFile: string;
    sections: Array<{
      sectionId: string;
      sectionTitle: string;
      content: ModuleContent;
    }>;
  }>;
  totalModules: number;
  totalSections: number;
}


export interface QuestionData {
  question_number: number;
  question: string;
  options: Record<string, string>;
  correct_answer: string;
  explanation: string;
}

export interface QAModule {
  id: string;
  title: string;
  description: string;
  questionCount: string;
  icon: ReactNode;
  color?: string;
  locked?: boolean;
  jsonFile: string;
}

export interface QAModuleResponse {
  moduleId: string;
  jsonFile: string;
  metadata?: {
    focus?: string;
    generated_at?: string;
    repository?: string;
  };
  questions: QuestionData[];
  totalQuestions: number;
}

export interface TutorialStep {
  step_number: number;
  title: string;
  code: string;
  language?: string;
  explanation?: string;
}

export interface PRTutorial {
  tutorial_number: number;
  pr_number: number;
  pr_title: string;
  author: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  code_files_modified: number;
  brief_description: string;
  type: string;
  raw_response: string;
  sections?: any;
  code_blocks_count?: number;
  total_code_lines?: number;
  pr_selection_response?: string;
}

export interface CodingQuestion {
  question_number: number;
  category: 'UI' | 'Feature' | 'Test';
  raw_response: string;
}

export interface PRTutorialsResponse {
  metadata: {
    generated_at: string;
    generator_version: string;
    provider: string;
    model: string;
    total_tutorials_requested: number;
    total_tutorials_generated: number;
  };
  tutorials: PRTutorial[];
  statistics: any;
}

export interface CodingQuestionsResponse {
  metadata: {
    generated_at: string;
    generator_version: string;
    provider: string;
    model: string;
    total_questions_requested: number;
    total_questions_generated: number;
    categories: string[];
  };
  questions: CodingQuestion[];
}
