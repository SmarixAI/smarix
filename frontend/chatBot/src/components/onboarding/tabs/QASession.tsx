'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { MessageSquare, ChevronDown, CheckCircle2, XCircle, Send, Award, Trophy } from 'lucide-react';
import { QAService } from '../services/QASession/contentService';
import type { QuestionData } from '../../../../types/onboarding';

interface QASessionProps {
  darkMode: boolean;
  selectedSection?: string | null;
  employeeId?: string | null;
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

interface ModuleData {
  moduleId: string;
  title: string;
  icon: string;
  color: string;
  questions: QuestionData[];
  isExpanded: boolean;
}

export default function QASession({ darkMode, selectedSection, employeeId, onboardingData, onUpdateProgress }: QASessionProps) {
  const [modules, setModules] = useState<ModuleData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: string]: string }>({});
  const [submittedAnswers, setSubmittedAnswers] = useState<{ [key: string]: string }>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const moduleConfig = [
    { id: 'overview', title: 'Project Overview', icon: '📋', color: 'from-indigo-400 to-blue-500' },
    { id: 'tech_stack', title: 'Tech Stack', icon: '⚙️', color: 'from-violet-400 to-purple-500' },
    { id: 'repo_structure', title: 'Repo Structure', icon: '📁', color: 'from-cyan-400 to-teal-500' },
    { id: 'app_features', title: 'App Features', icon: '✨', color: 'from-amber-400 to-orange-500' },
    { id: 'dev_setup', title: 'Dev Setup', icon: '🔧', color: 'from-emerald-400 to-green-500' },
    { id: 'code_conventions', title: 'Code Conventions', icon: '📝', color: 'from-rose-400 to-pink-500' },
  ];

  useEffect(() => {
    const fetchAllModules = async () => {
      setIsLoading(true);
      const loadedModules: ModuleData[] = [];

      // If selectedSection is provided, only fetch that section
      const modulesToFetch = selectedSection 
        ? moduleConfig.filter(config => config.id === selectedSection)
        : moduleConfig;

      for (const config of modulesToFetch) {
        // Try to fetch from new API first (using module id like 'overview', 'tech_stack', etc.)
        try {
          const response = await fetch(`/api/onboarding/qa/${config.id}`);
          if (response.ok) {
            const data = await response.json();
            if (data.questions && data.questions.length > 0) {
              loadedModules.push({
                moduleId: config.id,
                title: config.title,
                icon: config.icon,
                color: config.color,
                questions: data.questions,
                isExpanded: true, // Auto-expand if only one section
              });
              continue;
            }
          }
        } catch (e) {
          // Fallback to old service
        }

        // Fallback to old QAService
        const response = await QAService.fetchQAModule(config.id);
        if (response) {
          loadedModules.push({
            moduleId: config.id,
            title: config.title,
            icon: config.icon,
            color: config.color,
            questions: response.questions,
            isExpanded: !selectedSection || config.id === selectedSection,
          });
        }
      }

      setModules(loadedModules);
      setIsLoading(false);
    };

    fetchAllModules();
  }, [selectedSection, employeeId]);

  const toggleModule = useCallback((moduleId: string) => {
    setModules((prev) =>
      prev.map((m) =>
        m.moduleId === moduleId ? { ...m, isExpanded: !m.isExpanded } : m
      )
    );
  }, []);

  const handleAnswerSelect = useCallback((questionKey: string, option: string) => {
    if (isSubmitted) return;
    
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionKey]: option,
    }));
  }, [isSubmitted]);

  const handleSubmit = useCallback(async () => {
    if (!employeeId || !onUpdateProgress) {
      setSubmittedAnswers(selectedAnswers);
      setIsSubmitted(true);
      setShowResults(true);
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      return;
    }

    setSubmittedAnswers(selectedAnswers);
    setIsSubmitted(true);
    setShowResults(true);
    
    // Calculate scores per module and update progress
    const modulesToUpdate = selectedSection 
      ? modules.filter(m => m.moduleId === selectedSection)
      : modules;

    for (const module of modulesToUpdate) {
      let correctAnswers = 0;
      let totalQuestions = module.questions.length;

      module.questions.forEach((q) => {
        const qKey = `${module.moduleId}-${q.question_number}`;
        const userAnswer = selectedAnswers[qKey];
        if (userAnswer === q.correct_answer) {
          correctAnswers++;
        }
      });

      const score = correctAnswers;
      const progress = totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 0;
      const status = progress === 100 ? 'completed' : progress > 0 ? 'in-progress' : 'pending';

      // Update progress for this module
      await onUpdateProgress('qa', module.moduleId, {
        id: module.moduleId,
        title: module.title,
        status,
        score,
        totalQuestions,
        progress,
      });
    }
    
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }, [selectedAnswers, employeeId, onUpdateProgress, selectedSection, modules]);

  const handleReset = useCallback(() => {
    setSelectedAnswers({});
    setSubmittedAnswers({});
    setIsSubmitted(false);
    setShowResults(false);
  }, []);

  // Calculate overall stats (all modules)
  const overallStats = useMemo(() => {
    const totalQuestions = modules.reduce((sum, m) => sum + m.questions.length, 0);
    const answeredQuestions = Object.keys(selectedAnswers).length;
    
    let correctAnswers = 0;
    let incorrectAnswers = 0;
    
    if (isSubmitted) {
      modules.forEach((module) => {
        module.questions.forEach((q) => {
          const qKey = `${module.moduleId}-${q.question_number}`;
          const userAnswer = submittedAnswers[qKey];
          if (userAnswer === q.correct_answer) {
            correctAnswers++;
          } else if (userAnswer) {
            incorrectAnswers++;
          }
        });
      });
    }

    const answeredProgress = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
    const scorePercentage = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;

    return {
      totalQuestions,
      answeredQuestions,
      correctAnswers,
      incorrectAnswers,
      unanswered: totalQuestions - answeredQuestions,
      answeredProgress,
      scorePercentage,
    };
  }, [modules, selectedAnswers, submittedAnswers, isSubmitted]);

  // Calculate current section stats (selected section only)
  const currentSectionStats = useMemo(() => {
    if (!selectedSection) {
      return overallStats;
    }

    const filteredModules = modules.filter(m => m.moduleId === selectedSection);
    const totalQuestions = filteredModules.reduce((sum, m) => sum + m.questions.length, 0);
    const answeredQuestions = Object.keys(selectedAnswers).filter(key => 
      key.startsWith(`${selectedSection}-`)
    ).length;
    
    let correctAnswers = 0;
    let incorrectAnswers = 0;
    
    if (isSubmitted) {
      filteredModules.forEach((module) => {
        module.questions.forEach((q) => {
          const qKey = `${module.moduleId}-${q.question_number}`;
          const userAnswer = submittedAnswers[qKey];
          if (userAnswer === q.correct_answer) {
            correctAnswers++;
          } else if (userAnswer) {
            incorrectAnswers++;
          }
        });
      });
    }

    const answeredProgress = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
    const scorePercentage = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;

    return {
      totalQuestions,
      answeredQuestions,
      correctAnswers,
      incorrectAnswers,
      unanswered: totalQuestions - answeredQuestions,
      answeredProgress,
      scorePercentage,
    };
  }, [modules, selectedAnswers, submittedAnswers, isSubmitted, selectedSection, overallStats]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-in-right">
      {/* Concise Header */}
      <div className="mb-3">
        <h2 className={`text-xl font-bold mb-1 ${
          darkMode
            ? 'bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent'
            : 'bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent'
        }`}>
          Q&A Knowledge Check
        </h2>
        <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
          Test your understanding section by section. Click on each section to expand and answer questions.
        </p>
      </div>

      {/* Reset button when submitted */}
      {isSubmitted && (
        <div className="flex justify-end mb-4">
          <button
            onClick={handleReset}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              darkMode
                ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
            }`}
          >
            Reset
          </button>
        </div>
      )}

      <div className="space-y-4">
        {(selectedSection ? modules.filter(m => m.moduleId === selectedSection) : modules).map((module) => (
          <div
            key={module.moduleId}
            className={`rounded-2xl overflow-hidden transition-all ${
              darkMode
                ? 'bg-gray-800/50 ring-1 ring-gray-700'
                : 'bg-white/80 ring-1 ring-slate-200'
            }`}
          >
            <button
              onClick={() => toggleModule(module.moduleId)}
              className={`w-full px-6 py-5 flex items-center justify-between transition-all ${
                darkMode ? 'hover:bg-gray-800/80' : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-4">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br ${module.color} shadow-lg`}
                >
                  <span className="text-2xl">{module.icon}</span>
                </div>
                <div className="text-left">
                  <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                    {module.title}
                  </h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                    {module.questions.length} Questions
                  </p>
                </div>
              </div>

              <ChevronDown
                className={`w-6 h-6 transition-transform ${
                  module.isExpanded ? 'rotate-180' : ''
                } ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}
              />
            </button>

            {module.isExpanded && (
              <div className={`px-6 py-4 border-t ${darkMode ? 'border-gray-700' : 'border-slate-200'}`}>
                <div className="space-y-6">
                  {module.questions.map((question) => {
                    const qKey = `${module.moduleId}-${question.question_number}`;
                    const selectedOption = selectedAnswers[qKey];
                    const submittedOption = submittedAnswers[qKey];
                    const isCorrect = submittedOption === question.correct_answer;

                    return (
                      <div
                        key={question.question_number}
                        className={`p-5 rounded-xl ${
                          darkMode
                            ? 'bg-gray-900/50 border border-gray-700'
                            : 'bg-indigo-50/50 border border-indigo-200'
                        }`}
                      >
                        <p
                          className={`font-semibold text-base mb-4 ${
                            darkMode ? 'text-white' : 'text-slate-900'
                          }`}
                        >
                          {question.question_number}. {question.question}
                        </p>

                        <div className="space-y-3">
                          {Object.entries(question.options).map(([optKey, optText]) => {
                            const isSelected = selectedOption === optKey;
                            const isCorrectOption = optKey === question.correct_answer;
                            const showCorrect = isSubmitted && isCorrectOption;
                            const showWrong = isSubmitted && submittedOption === optKey && !isCorrect;

                            return (
                              <button
                                key={optKey}
                                onClick={() => handleAnswerSelect(qKey, optKey)}
                                disabled={isSubmitted}
                                className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-all ${
                                  showCorrect
                                    ? darkMode
                                      ? 'bg-green-600/30 border-green-400 text-green-200'
                                      : 'bg-green-100 border-green-500 text-green-900'
                                    : showWrong
                                    ? darkMode
                                      ? 'bg-red-600/30 border-red-400 text-red-200'
                                      : 'bg-red-100 border-red-500 text-red-900'
                                    : isSelected
                                    ? darkMode
                                      ? 'bg-blue-600/40 border-blue-400 text-white'
                                      : 'bg-indigo-200 border-indigo-500 text-slate-900'
                                    : darkMode
                                    ? 'bg-gray-800/50 border-gray-700 text-gray-200 hover:bg-gray-800/70'
                                    : 'bg-white border-gray-300 text-slate-700 hover:bg-indigo-50'
                                } ${isSubmitted ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                              >
                                <div className="flex items-center justify-between">
                                  <span>
                                    <strong>{optKey}:</strong> {optText as string}
                                  </span>
                                  {showCorrect && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                                  {showWrong && <XCircle className="w-5 h-5 text-red-500" />}
                                </div>
                              </button>
                            );
                          })}
                        </div>

                        {isSubmitted && (
                          <div
                            className={`mt-4 p-4 rounded-lg ${
                              darkMode
                                ? 'bg-gray-900/50 text-gray-200 border border-gray-700'
                                : 'bg-white text-slate-800 border border-gray-200'
                            }`}
                          >
                            <p
                              className={`font-semibold mb-2 ${
                                darkMode ? 'text-green-300' : 'text-green-700'
                              }`}
                            >
                              Correct Answer: <strong>{question.correct_answer}</strong>
                            </p>
                            <p className="text-sm leading-relaxed">{question.explanation}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {!isSubmitted && overallStats.answeredQuestions > 0 && (
        <div className="sticky bottom-6 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={overallStats.answeredQuestions === 0}
            className={`px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 active:scale-95 shadow-2xl flex items-center space-x-3 ${
              overallStats.answeredQuestions === overallStats.totalQuestions
                ? darkMode
                  ? 'bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 hover:from-green-500 hover:via-emerald-500 hover:to-teal-500 text-white'
                  : 'bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 hover:from-green-600 hover:via-emerald-600 hover:to-teal-600 text-white'
                : darkMode
                ? 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white'
                : 'bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500 hover:from-indigo-600 hover:via-cyan-600 hover:to-teal-600 text-white'
            }`}
          >
            <Send className="w-6 h-6" />
            <span>
              Submit {overallStats.answeredQuestions === overallStats.totalQuestions ? 'All' : ''} Answers
              {overallStats.answeredQuestions !== overallStats.totalQuestions &&
                ` (${overallStats.answeredQuestions}/${overallStats.totalQuestions})`}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}
