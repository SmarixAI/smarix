import { FileText, Code, BookOpen, Wrench, Lock, Sparkles, Zap } from 'lucide-react';
import type { Module } from '../../../../../types/onboarding';

// Mapping from numeric IDs to string names (for backward compatibility)
export const MODULE_ID_TO_NAME: { [key: string]: string } = {
  '1': 'overview',
  '2': 'tech_stack',
  '3': 'repo_structure',
  '4': 'app_features',
  '5': 'dev_setup',
  '6': 'code_conventions',
};

// Mapping from string names to file names
export const MODULE_FILE_MAPPING: { [key: string]: string } = {
  // String IDs (primary naming convention)
  'overview': 'onboarding_project_overview.json',
  'tech_stack': 'onboarding_tech_stack.json',
  'repo_structure': 'onboarding_repo_structure.json',
  'app_features': 'onboarding_app_features.json',
  'dev_setup': 'onboarding_dev_setup.json',
  'code_conventions': 'onboarding_code_conventions.json',
  // Numeric IDs (for backward compatibility - maps to string names first)
  '1': 'onboarding_project_overview.json',
  '2': 'onboarding_tech_stack.json',
  '3': 'onboarding_repo_structure.json',
  '4': 'onboarding_app_features.json',
  '5': 'onboarding_dev_setup.json',
  '6': 'onboarding_code_conventions.json',
};

// Helper function to convert numeric ID to string name
export const getModuleName = (moduleId: string): string => {
  return MODULE_ID_TO_NAME[moduleId] || moduleId;
};

export const modules: Module[] = [
  {
    id: 'overview',
    title: 'Project Overview',
    description: 'Learn about the platform architecture, core features, and how everything connects together',
    duration: '10 mins',
    icon: <FileText className="w-6 h-6" />,
    color: '#3B82F6', // Blue - matching landing page onboarding color
    jsonFile: MODULE_FILE_MAPPING['overview'],
  },
  {
    id: 'tech_stack',
    title: 'Tech Stacks',
    description: 'Explore the modern technology stack including frameworks, databases, and infrastructure tools',
    duration: '15 mins',
    icon: <Code className="w-6 h-6" />,
    color: '#6366F1', // Indigo - matching landing page offboarding color
    jsonFile: MODULE_FILE_MAPPING['tech_stack'],
  },
  {
    id: 'repo_structure',
    title: 'Repo Structure',
    description: 'Navigate the codebase organization, folder hierarchy, and module dependencies',
    duration: '12 mins',
    icon: <FileText className="w-6 h-6" />,
    color: '#06B6D4', // Cyan - matching landing page gradient colors
    jsonFile: MODULE_FILE_MAPPING['repo_structure'],
  },
  {
    id: 'app_features',
    title: 'App Features',
    description: 'Discover key features, user flows, and integration points across the application',
    duration: '20 mins',
    icon: <Sparkles className="w-6 h-6" />,
    color: '#10B981', // Green - matching landing page assistance color
    jsonFile: MODULE_FILE_MAPPING['app_features'],
  },
  {
    id: 'dev_setup',
    title: 'Dev Setup',
    description: 'Clone repository, install dependencies, configure environment, and run local development server',
    duration: '30 mins',
    icon: <Wrench className="w-6 h-6" />,
    color: '#8B5CF6', // Purple - matching landing page gradient colors
    jsonFile: MODULE_FILE_MAPPING['dev_setup'],
  },
  {
    id: 'code_conventions',
    title: 'Code Conventions',
    description: 'Follow style guidelines, naming patterns, Git workflow, and PR best practices',
    duration: '15 mins',
    icon: <Zap className="w-6 h-6" />,
    color: '#3B82F6', // Blue - reusing primary blue
    jsonFile: MODULE_FILE_MAPPING['code_conventions'],
  },
];
