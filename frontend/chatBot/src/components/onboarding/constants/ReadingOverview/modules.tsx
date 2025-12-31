import { FileText, Code, BookOpen, Wrench, Lock, Sparkles, Zap } from 'lucide-react';
import type { Module } from '../../../../../types/onboarding';

export const MODULE_FILE_MAPPING: { [key: string]: string } = {
  '1': 'onboarding_project_overview.json',
  '2': 'onboarding_tech_stack.json',
  '3': 'onboarding_repo_structure.json',
  '4': 'onboarding_app_features.json',
  '5': 'onboarding_dev_setup.json',
  '6': 'onboarding_code_conventions.json',
};

export const modules: Module[] = [
  {
    id: '1',
    title: 'Project Overview',
    description: 'Learn about the platform architecture, core features, and how everything connects together',
    duration: '10 mins',
    icon: <FileText className="w-6 h-6" />,
    color: 'from-indigo-400 to-blue-500',
    jsonFile: MODULE_FILE_MAPPING['1'],
  },
  {
    id: '2',
    title: 'Tech Stacks',
    description: 'Explore the modern technology stack including frameworks, databases, and infrastructure tools',
    duration: '15 mins',
    icon: <Code className="w-6 h-6" />,
    color: 'from-violet-400 to-purple-500',
    jsonFile: MODULE_FILE_MAPPING['2'],
  },
  {
    id: '3',
    title: 'Repo Structure',
    description: 'Navigate the codebase organization, folder hierarchy, and module dependencies',
    duration: '12 mins',
    icon: <FileText className="w-6 h-6" />,
    color: 'from-cyan-400 to-teal-500',
    jsonFile: MODULE_FILE_MAPPING['3'],
  },
  {
    id: '4',
    title: 'App Features',
    description: 'Discover key features, user flows, and integration points across the application',
    duration: '20 mins',
    icon: <Sparkles className="w-6 h-6" />,
    color: 'from-amber-400 to-orange-500',
    jsonFile: MODULE_FILE_MAPPING['4'],
  },
  {
    id: '5',
    title: 'Dev Setup',
    description: 'Clone repository, install dependencies, configure environment, and run local development server',
    duration: '30 mins',
    icon: <Wrench className="w-6 h-6" />,
    color: 'from-emerald-400 to-green-500',
    jsonFile: MODULE_FILE_MAPPING['5'],
  },
  {
    id: '6',
    title: 'Code Conventions',
    description: 'Follow style guidelines, naming patterns, Git workflow, and PR best practices',
    duration: '15 mins',
    icon: <Zap className="w-6 h-6" />,
    color: 'from-rose-400 to-pink-500',
    jsonFile: MODULE_FILE_MAPPING['6'],
  },
];
