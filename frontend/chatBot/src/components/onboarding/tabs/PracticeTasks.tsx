'use client';

import { useEffect, useState } from "react";
import {
  ChevronLeft, 
  ChevronRight, 
  Code, 
  Check, 
  Shield 
} from "lucide-react";
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface PracticeTasksProps {
  darkMode: boolean;
  tasks?: any[];
  openTask?: number | null;
  onSelectTask?: (n: number | null) => void;
  employeeId?: string | null;
  activeRepos?: string[];
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

export default function PracticeTasks({
  darkMode,
  tasks,
  openTask,
  onSelectTask,
  employeeId,
  activeRepos = [],
  onUpdateProgress,
}: PracticeTasksProps) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [practicedMap, setPracticedMap] = useState<Record<number, boolean>>({});
  const [expandedCode, setExpandedCode] = useState<Record<string, boolean>>({});
  const [activeStepMap, setActiveStepMap] = useState<Record<number, number>>({});

  useEffect(() => {
    if (openTask !== undefined && openTask !== null && !activeStepMap[openTask]) {
      setActiveStepMap((p) => ({ ...p, [openTask]: 0 }));
    }
  }, [openTask]);

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      setError(null);

      if (tasks && tasks.length > 0) {
        const hasFullContent = tasks.some((task: any) => 
          task.steps && Array.isArray(task.steps) && task.steps.length > 0
        );
        
        if (hasFullContent) {
          setData({ questions: tasks });
          setLoading(false);
          return;
        }

        try {
          const response = await fetch("/api/onboarding/practice/practice1");
          if (response.ok) {
            const json = await response.json();
            const allFullTasks = json.tasks || json.questions || [];
            
            const fullTasks = tasks.map((task: any) => {
              const fullTask = allFullTasks.find((t: any) => t.question_number === task.question_number);
              return fullTask ? { ...fullTask, ...task } : task;
            });
            
            setData({ questions: fullTasks });
            setLoading(false);
            return;
          }
        } catch (e) {
          console.error('Fetch error:', e);
        }
        
        setData({ questions: tasks });
        setLoading(false);
        return;
      }

      // Use the first active repo if available
      const repo = activeRepos && activeRepos.length > 0 ? activeRepos[0] : undefined;
      const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';
      
      try {
        const response = await fetch(`/api/onboarding/practice/practice1${repoParam}`);
        if (response.ok) {
          const json = await response.json();
          setData({ questions: json.tasks || json.questions || [] });
        } else {
          setError("Failed to load practice tasks");
        }
      } catch (e) {
        setError("Failed to load practice tasks");
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [tasks]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("onboard_practice_progress");
      if (raw) setPracticedMap(JSON.parse(raw));
    } catch {}
  }, []);

  const toggleCodeView = (taskNum: number, stepNum: number) => {
    const key = `${taskNum}-${stepNum}`;
    setExpandedCode((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const markTaskComplete = (taskNum: number) => {
    const updated = { ...practicedMap, [taskNum]: true };
    setPracticedMap(updated);
    localStorage.setItem("onboard_practice_progress", JSON.stringify(updated));
  };

  if (loading) {
    return <div className="p-4 flex items-center justify-center min-h-[300px]">Loading practice tasks…</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500 text-center">{error}</div>;
  }

  if (!data || !data.questions || data.questions.length === 0) {
    return (
      <div className="p-4 text-center min-h-[300px] flex flex-col items-center justify-center text-gray-500">
        No practice tasks available
      </div>
    );
  }

  const filteredTasks = openTask !== null && openTask !== undefined
    ? data.questions.filter((task: any) => task.question_number === openTask)
    : data.questions;

  if (filteredTasks.length === 0) {
    return (
      <div className={`p-8 text-center min-h-[300px] flex flex-col items-center justify-center rounded-xl border-2 ${
        darkMode ? 'border-orange-500/30 bg-gradient-to-br from-orange-900/20' : 'border-orange-400/30 bg-gradient-to-br from-orange-50/40'
      }`}>
        <Shield className="w-12 h-12 text-orange-400 mb-4" />
        <p className={`text-xl font-bold mb-1 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
          No task selected
        </p>
        <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
          Select a task from the sidebar
        </p>
      </div>
    );
  }

  return (
    <div className="w-full p-2 lg:p-4 h-full overflow-hidden">
      <div className="h-full flex flex-col max-w-none">
        {filteredTasks.map((task: any) => {
          const isCompleted = practicedMap[task.question_number];
          const idx = activeStepMap[task.question_number] ?? 0;
          const total = task.steps?.length || 1;
          const step = task.steps?.[idx];
          const key = `${task.question_number}-${step?.step_number || 1}`;

          return (
            <div key={task.question_number} className="h-full flex flex-col space-y-3 lg:space-y-4">
              {/* TASK OVERVIEW */}
              <div className={`rounded-xl border-2 p-4 flex-shrink-0 overflow-hidden shadow-sm ${
                darkMode 
                  ? 'border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-indigo-900/20' 
                  : 'border-purple-300/40 bg-gradient-to-br from-purple-50/60 to-indigo-50/60'
              }`}>
                <div className="flex items-start justify-between mb-2">
                  <h3 className={`text-base font-bold ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                    {task.title || `Task #${task.question_number}`}
                  </h3>
                  {isCompleted && (
                    <div className={`px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${
                      darkMode ? 'bg-green-500/20 text-green-300 border border-green-500/30' : 'bg-green-500/10 text-green-700 border border-green-300/50'
                    }`}>
                      <Check className="w-3 h-3" />
                      Completed
                    </div>
                  )}
                </div>
                <p className={`text-sm leading-relaxed line-clamp-2 ${darkMode ? 'text-gray-300' : 'text-slate-600'}`}>
                  {task.question_description || 'Android Development Practice'}
                </p>
              </div>

              {/* STEPS CONTAINER */}
              {task.steps && task.steps.length > 0 ? (
                <div className={`flex-1 flex flex-col rounded-2xl border-2 overflow-hidden shadow-lg ${
                  darkMode 
                    ? 'border-orange-500/30 bg-gradient-to-br from-orange-900/20 to-amber-900/20' 
                    : 'border-orange-300/40 bg-gradient-to-br from-orange-50/60 to-amber-50/60'
                }`}>
                  {/* Progress Header */}
                  <div className={`px-5 py-4 border-b flex-shrink-0 ${
                    darkMode ? 'bg-gray-800/90 border-orange-500/30' : 'bg-white/95 border-orange-200/40'
                  }`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-md ${
                          darkMode ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white' : 'bg-gradient-to-r from-orange-500 to-orange-600 text-white'
                        }`}>
                          <span className="font-bold text-lg">{idx + 1}</span>
                        </div>
                        <div>
                          <p className={`text-sm font-semibold ${darkMode ? 'text-gray-100' : 'text-slate-800'}`}>
                            Step {idx + 1} of {total}
                          </p>
                          <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                            {step.step_title}
                          </p>
                        </div>
                      </div>
                      <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                        darkMode 
                          ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' 
                          : 'bg-orange-500/20 text-orange-700 border border-orange-400/50'
                      }`}>
                        {Math.round(((idx + 1) / total) * 100)}%
                      </span>
                    </div>
                    
                    <div className="flex space-x-1">
                      {Array.from({ length: total }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 flex-1 rounded-full transition-all duration-500 shadow-sm ${
                            i < idx + 1 
                              ? 'bg-gradient-to-r from-orange-500 to-orange-600' 
                              : darkMode ? 'bg-gray-700/50' : 'bg-gray-200/60'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Scrollable Content */}
                  <div className="flex-1 flex flex-col px-5 py-5 overflow-hidden">
                    <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200 dark:scrollbar-thumb-gray-600 dark:scrollbar-track-gray-800">
                      
                      {/* What to implement */}
                      <div className={`rounded-xl border p-4 shadow-sm ${
                        darkMode 
                          ? 'border-blue-500/30 bg-gradient-to-br from-blue-900/20 to-blue-800/20' 
                          : 'border-blue-300/40 bg-gradient-to-br from-blue-50/70 to-blue-50/60'
                      }`}>
                        <h4 className={`text-sm font-bold mb-3 flex items-center gap-2 ${
                          darkMode ? 'text-blue-300' : 'text-blue-700'
                        }`}>
                          What to implement
                        </h4>
                        <div className={`prose prose-sm max-w-none ${darkMode ? 'prose-invert' : ''}`}>
                          <ReactMarkdown>
                            {step.implementation_details || 'No implementation details provided.'}
                          </ReactMarkdown>
                        </div>
                      </div>

                      {/* Enhanced Code Section */}
                      <div className={`rounded-xl border-2 cursor-pointer transition-all duration-200 hover:shadow-md overflow-hidden group ${
                        expandedCode[key]
                          ? darkMode 
                            ? 'border-emerald-500/50 bg-gradient-to-br from-emerald-900/30 to-green-900/30 shadow-emerald-500/10' 
                            : 'border-emerald-400/60 bg-gradient-to-br from-emerald-50/80 to-green-50/70 shadow-emerald-300/20'
                          : darkMode 
                            ? 'border-gray-600/50 hover:border-gray-500/70 bg-gray-800/60 hover:bg-gray-700/70' 
                            : 'border-gray-200/60 hover:border-gray-300/80 bg-white/90 hover:bg-white'
                      }`} 
                        onClick={() => toggleCodeView(task.question_number, step.step_number)}
                      >
                        <div className={`px-4 py-3 border-b flex items-center justify-between group-hover:bg-opacity-90 transition-all ${
                          darkMode 
                            ? 'bg-gray-800/95 border-gray-600/30' 
                            : expandedCode[key] ? 'bg-emerald-50/80 border-emerald-200/50' : 'bg-white border-gray-200/30'
                        }`}>
                          <div className="flex items-center gap-2">
                            <Code className={`w-4 h-4 ${expandedCode[key] ? 'text-emerald-400' : 'text-gray-600'}`} />
                            <span className={`text-sm font-semibold ${
                              expandedCode[key] 
                                ? darkMode ? 'text-emerald-300' : 'text-emerald-700' 
                                : darkMode ? 'text-gray-200' : 'text-slate-800'
                            }`}>
                              {expandedCode[key] ? "Solution Code" : "View Solution Code"}
                            </span>
                          </div>
                          <ChevronRight className={`w-5 h-5 transition-transform duration-300 ${
                            expandedCode[key] ? 'rotate-90 text-emerald-400' : 'text-gray-500'
                          }`} />
                        </div>
                        
                        {expandedCode[key] && step.code_snippet && (
                          <div className={`p-4 max-h-64 overflow-y-auto`}>
                            <SyntaxHighlighter
                              language="java"
                              style={darkMode ? vscDarkPlus : oneLight}
                              customStyle={{
                                borderRadius: '0.75rem',
                                padding: '1.25rem !important',
                                fontSize: '0.875rem',
                                margin: '0 !important',
                                border: '1px solid transparent',
                                background: darkMode ? '#1e1e1e' : '#f8fafc',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                overflow: 'visible',
                              }}
                            >
                              {step.code_snippet}
                            </SyntaxHighlighter>
                          </div>
                        )}
                      </div>

                      {/* Tips */}
                      {step.tips && step.tips.length > 0 && (
                        <div className={`rounded-xl border p-4 shadow-sm ${
                          darkMode 
                            ? 'border-yellow-500/30 bg-gradient-to-br from-yellow-900/20 to-amber-900/20' 
                            : 'border-yellow-300/40 bg-gradient-to-br from-yellow-50/70 to-amber-50/60'
                        }`}>
                          <h4 className={`text-sm font-bold mb-3 flex items-center gap-2 ${
                            darkMode ? 'text-yellow-300' : 'text-yellow-700'
                          }`}>
                            Tips
                          </h4>
                          <div className="space-y-2">
                            {step.tips.map((tip: string, i: number) => (
                              <div key={i} className={`flex items-start gap-3 p-2.5 rounded-lg bg-yellow-500/5 border ${
                                darkMode ? 'border-yellow-500/20' : 'border-yellow-200/30'
                              }`}>
                                <div className={`w-2 h-2 mt-2 rounded-full bg-yellow-400 flex-shrink-0`} />
                                <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>
                                  {tip}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Common Mistakes */}
                      {step.common_mistakes && step.common_mistakes.length > 0 && (
                        <div className={`rounded-xl border p-4 shadow-sm ${
                          darkMode 
                            ? 'border-red-500/30 bg-gradient-to-br from-red-900/20 to-rose-900/20' 
                            : 'border-red-300/40 bg-gradient-to-br from-red-50/70 to-rose-50/60'
                        }`}>
                          <h4 className={`text-sm font-bold mb-3 flex items-center gap-2 ${
                            darkMode ? 'text-red-300' : 'text-red-700'
                          }`}>
                            Common Mistakes
                          </h4>
                          <div className="space-y-2">
                            {step.common_mistakes.map((mistake: string, i: number) => (
                              <div key={i} className={`flex items-start gap-3 p-2.5 rounded-lg bg-red-500/5 border ${
                                darkMode ? 'border-red-500/20' : 'border-red-200/30'
                              }`}>
                                <div className={`w-2 h-2 mt-2 rounded-full bg-red-400 flex-shrink-0`} />
                                <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>
                                  {mistake}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Navigation */}
                  <div className={`px-5 py-4 border-t flex-shrink-0 flex items-center justify-between ${
                    darkMode 
                      ? 'bg-gray-800/90 border-orange-500/20 backdrop-blur-sm' 
                      : 'bg-white/95 border-orange-200/30 backdrop-blur-sm'
                  }`}>
                    <button
                      onClick={() => setActiveStepMap((p) => ({
                        ...p,
                        [task.question_number]: Math.max(0, idx - 1),
                      }))}
                      disabled={idx === 0}
                      className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all shadow-sm ${
                        idx === 0
                          ? 'bg-gray-500/30 text-gray-400 cursor-not-allowed' 
                          : darkMode
                            ? 'bg-gray-700/70 text-gray-200 hover:bg-gray-600/80 border border-gray-500/50 hover:scale-105'
                            : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300/50 hover:scale-105'
                      }`}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Previous</span>
                    </button>

                    <div className="flex items-center gap-2">
                      {Array.from({ length: total }).map((_, i) => (
                        <button
                          key={i}
                          onClick={() => setActiveStepMap((p) => ({ ...p, [task.question_number]: i }))}
                          className={`w-3 h-3 rounded-full transition-all shadow-sm ${
                            i === idx
                              ? 'bg-gradient-to-r from-orange-500 to-orange-600 w-10 scale-110 shadow-orange-500/50'
                              : i < idx
                              ? 'bg-orange-400'
                              : darkMode 
                              ? 'bg-gray-600 hover:bg-gray-500' 
                              : 'bg-gray-300 hover:bg-gray-400'
                          }`}
                        />
                      ))}
                    </div>

                    {idx === total - 1 ? (
                      !isCompleted ? (
                        <button
                          onClick={() => markTaskComplete(task.question_number)}
                          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-bold shadow-lg hover:from-emerald-700 hover:to-green-700 hover:scale-105 transition-all"
                        >
                          Mark Complete
                        </button>
                      ) : (
                        <div className={`px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 shadow-md ${
                          darkMode 
                            ? 'bg-emerald-500/20 text-emerald-300 border-2 border-emerald-500/40' 
                            : 'bg-emerald-500/10 text-emerald-700 border-2 border-emerald-400/60'
                        }`}>
                          <Check className="w-4 h-4" />
                          Completed
                        </div>
                      )
                    ) : (
                      <button
                        onClick={() => setActiveStepMap((p) => ({
                          ...p,
                          [task.question_number]: idx + 1,
                        }))}
                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white text-sm font-bold shadow-lg hover:from-orange-600 hover:to-orange-700 hover:scale-105 transition-all"
                      >
                        Next Step
                        <ChevronRight className="w-4 h-4 ml-1 inline" />
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className={`flex-1 rounded-xl border-2 p-8 text-center flex flex-col items-center justify-center ${
                  darkMode ? 'border-gray-600/50 bg-gray-900/50' : 'border-gray-200/50 bg-gray-50/50'
                }`}>
                  <Shield className={`w-12 h-12 opacity-40 mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  <p className={`text-lg font-medium ${darkMode ? 'text-gray-300' : 'text-slate-600'}`}>
                    No steps available
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
