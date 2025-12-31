import { FileText, Code, BookOpen, Wrench, Lock, Sparkles } from 'lucide-react';
import type { QAModule } from '../../../../../types/onboarding';

export const QA_MODULE_FILE_MAPPING: { [key: string]: string } = {
  '1': 'onboarding_overview_questions.json',
  '2': 'onboarding_tech_stack_questions.json',
  '3': 'onboarding_repo_structure_questions.json',
  '4': 'onboarding_app_features_questions.json',
  '5': 'onboarding_dev_setup_questions.json',
  '6': 'onboarding_code_conventions_questions.json',
};

export const qaModules: QAModule[] = [
  {
    id: '1',
    title: 'Project Overview',
    description: 'Test your understanding of the platform architecture and core features',
    questionCount: '10 questions',
    icon: <FileText className="w-6 h-6" />,
    color: 'from-indigo-400 to-blue-500',
    jsonFile: QA_MODULE_FILE_MAPPING['1'],
  },
  {
    id: '2',
    title: 'Tech Stack',
    description: 'Verify your knowledge of frameworks, databases, and infrastructure tools',
    questionCount: '12 questions',
    icon: <Code className="w-6 h-6" />,
    color: 'from-violet-400 to-purple-500',
    jsonFile: QA_MODULE_FILE_MAPPING['2'],
  },
  {
    id: '3',
    title: 'Repo Structure',
    description: 'Check your understanding of codebase organization and module dependencies',
    questionCount: '8 questions',
    icon: <FileText className="w-6 h-6" />,
    color: 'from-cyan-400 to-teal-500',
    jsonFile: QA_MODULE_FILE_MAPPING['3'],
  },
  {
    id: '4',
    title: 'App Features',
    description: 'Assess your knowledge of key features, user flows, and integrations',
    questionCount: '15 questions',
    icon: <Sparkles className="w-6 h-6" />,
    color: 'from-amber-400 to-orange-500',
    jsonFile: QA_MODULE_FILE_MAPPING['4'],
  },
  {
    id: '5',
    title: 'Dev Setup',
    description: 'Test your understanding of development environment and configuration',
    questionCount: '10 questions',
    icon: <Wrench className="w-6 h-6" />,
    color: 'from-emerald-400 to-green-500',
    jsonFile: QA_MODULE_FILE_MAPPING['5'],
  },
  {
    id: '6',
    title: 'Code Conventions',
    description: 'Verify your knowledge of style guidelines and best practices',
    questionCount: '12 questions',
    icon: <Lock className="w-6 h-6" />,
    color: 'from-rose-400 to-pink-500',
    jsonFile: QA_MODULE_FILE_MAPPING['6'],
  },
];
