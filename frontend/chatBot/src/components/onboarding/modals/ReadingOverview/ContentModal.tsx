'use client';

import { useEffect, useState } from "react";
import {
  ChevronLeft, 
  ChevronRight, 
  Code, 
  Check, 
  Shield,
  Lightbulb,
  AlertTriangle,
  Target
} from "lucide-react";
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Inter, JetBrains_Mono } from 'next/font/google';

interface PracticeTasksProps {
  tasks?: any[];
  openTask?: number | null;
  onSelectTask?: (n: number | null) => void;
  employeeId?: string | null;
  activeRepos?: string[];
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

export default function PracticeTasks({
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
    return (
      <div className="p-4 flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className={`${inter.className} text-sm text-slate-600 font-medium`}>Loading practice tasks…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${inter.className} p-4 text-red-600 text-center bg-red-50 rounded-xl border border-red-200 m-4`}>
        {error}
      </div>
    );
  }

  if (!data || !data.questions || data.questions.length === 0) {
    return (
      <div className="p-4 text-center min-h-[300px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
          <Shield className="w-8 h-8 text-slate-400" />
        </div>
        <p className={`${inter.className} text-lg font-semibold text-slate-700 mb-2`}>
          No practice tasks available
        </p>
      </div>
    );
  }

  const filteredTasks = openTask !== null && openTask !== undefined
    ? data.questions.filter((task: any) => task.question_number === openTask)
    : data.questions;

  if (filteredTasks.length === 0) {
    return (
      <div className="p-8 text-center min-h-[300px] flex flex-col items-center justify-center rounded-2xl border-2 border-slate-200 bg-white/60 backdrop-blur-sm m-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-100 to-blue-50 flex items-center justify-center mb-4">
          <Shield className="w-10 h-10 text-slate-400" />
        </div>
        <p className={`${inter.className} text-xl font-semibold mb-2 text-[#0E1B2E]`}>
          No task selected
        </p>
        <p className={`${inter.className} text-sm text-slate-600`}>
          Select a task from the sidebar to get started
        </p>
      </div>
    );
  }

  return (
    <div className="w-full p-4 lg:p-6 relative">
      <div className="relative z-10 space-y-5 lg:space-y-6">
        {filteredTasks.map((task: any) => {
          const isCompleted = practicedMap[task.question_number];
          const idx = activeStepMap[task.question_number] ?? 0;
          const total = task.steps?.length || 1;
          const step = task.steps?.[idx];
          const key = `${task.question_number}-${step?.step_number || 1}`;

          return (
            <div key={task.question_number} className="space-y-5 lg:space-y-6">
              {/* TASK OVERVIEW */}
              <div className="rounded-2xl border-2 border-slate-200 p-6 flex-shrink-0 bg-white/70 backdrop-blur-sm shadow-md shadow-slate-200/40">
                <div className="flex items-start justify-between mb-3">
                  <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}>
                    {task.title || `Task #${task.question_number}`}
                  </h3>
                  {isCompleted && (
                    <div className={`${inter.className} px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 bg-green-50 text-green-700 border-2 border-green-200 shadow-sm`}>
                      <Check className="w-4 h-4" />
                      Completed
                    </div>
                  )}
                </div>
                <p className={`${inter.className} text-[15px] leading-relaxed text-slate-700`}>
                  {task.question_description || 'Android Development Practice'}
                </p>
              </div>

              {/* STEPS CONTAINER */}
              {task.steps && task.steps.length > 0 ? (
                <div className="rounded-2xl border-2 border-slate-200 bg-white/70 backdrop-blur-sm shadow-lg shadow-slate-200/40 overflow-hidden">
                  {/* Progress Header */}
                  <div className="px-6 py-5 border-b-2 bg-gradient-to-r from-slate-50 to-blue-50/30 border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-[#0E1B2E] to-blue-900 text-white shadow-md">
                          <span className={`${jetbrainsMono.className} font-bold text-xl`}>{idx + 1}</span>
                        </div>
                        <div>
                          <p className={`${inter.className} text-sm font-semibold text-[#0E1B2E]`}>
                            Step {idx + 1} of {total}
                          </p>
                          <p className={`${inter.className} text-xs text-slate-600 font-medium`}>
                            {step.step_title}
                          </p>
                        </div>
                      </div>
                      <span className={`${jetbrainsMono.className} text-sm font-bold px-4 py-2 rounded-xl bg-blue-50 text-blue-700 border-2 border-blue-200 shadow-sm`}>
                        {Math.round(((idx + 1) / total) * 100)}%
                      </span>
                    </div>
                    
                    <div className="flex gap-2">
                      {Array.from({ length: total }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 flex-1 rounded-full transition-all duration-500 ${
                            i < idx + 1 
                              ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-600 shadow-sm' 
                              : 'bg-slate-200'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="px-6 py-6 space-y-5">
                      
                      {/* What to implement */}
                      <div className="rounded-xl border-2 border-blue-200/60 p-5 bg-gradient-to-br from-blue-50/50 to-white shadow-sm">
                        <h4 className={`${inter.className} text-sm font-bold mb-3 flex items-center gap-2 text-[#0E1B2E]`}>
                          <Target className="w-4 h-4 text-blue-600" />
                          What to implement
                        </h4>
                        <div className={`${inter.className} prose prose-sm max-w-none text-slate-700`}>
                          <ReactMarkdown>
                            {step.implementation_details || 'No implementation details provided.'}
                          </ReactMarkdown>
                        </div>
                      </div>

                      {/* Enhanced Code Section */}
                      <div className={`rounded-xl border-2 cursor-pointer transition-all duration-200 overflow-hidden ${
                        expandedCode[key]
                          ? 'border-slate-300 bg-slate-50 shadow-lg'
                          : 'border-slate-200 hover:border-slate-300 bg-white hover:shadow-md'
                      }`} 
                        onClick={() => toggleCodeView(task.question_number, step.step_number)}
                      >
                        <div className={`px-5 py-4 border-b-2 flex items-center justify-between transition-all ${
                          expandedCode[key] ? 'bg-gradient-to-r from-slate-800 to-slate-900 border-slate-700' : 'bg-gradient-to-r from-slate-50 to-white border-slate-200'
                        }`}>
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                              expandedCode[key] ? 'bg-white/10' : 'bg-slate-100'
                            }`}>
                              <Code className={`w-4 h-4 ${expandedCode[key] ? 'text-white' : 'text-slate-600'}`} />
                            </div>
                            <span className={`${inter.className} text-sm font-bold ${
                              expandedCode[key] ? 'text-white' : 'text-[#0E1B2E]'
                            }`}>
                              {expandedCode[key] ? "Solution Code" : "View Solution Code"}
                            </span>
                          </div>
                          <ChevronRight className={`w-5 h-5 transition-transform duration-300 ${
                            expandedCode[key] ? 'rotate-90 text-white' : 'text-slate-600'
                          }`} />
                        </div>
                        
                        {expandedCode[key] && step.code_snippet && (
                          <div className="p-5 bg-[#282c34]">
                            <SyntaxHighlighter
                              language="java"
                              style={oneDark}
                              customStyle={{
                                borderRadius: '0.75rem',
                                padding: '1.25rem',
                                fontSize: '0.875rem',
                                margin: '0',
                                background: '#282c34',
                              }}
                              showLineNumbers
                              wrapLines
                              codeTagProps={{
                                className: jetbrainsMono.className,
                              }}
                            >
                              {step.code_snippet}
                            </SyntaxHighlighter>
                          </div>
                        )}
                      </div>

                      {/* Tips */}
                      {step.tips && step.tips.length > 0 && (
                        <div className="rounded-xl border-2 border-amber-200/60 p-5 bg-gradient-to-br from-amber-50/50 to-white shadow-sm">
                          <h4 className={`${inter.className} text-sm font-bold mb-4 flex items-center gap-2 text-[#0E1B2E]`}>
                            <Lightbulb className="w-4 h-4 text-amber-600" />
                            Tips
                          </h4>
                          <div className="space-y-3">
                            {step.tips.map((tip: string, i: number) => (
                              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white border-2 border-amber-100">
                                <div className="w-6 h-6 mt-0.5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                                  <span className={`${jetbrainsMono.className} text-xs font-bold text-amber-700`}>{i + 1}</span>
                                </div>
                                <p className={`${inter.className} text-sm leading-relaxed text-slate-700`}>
                                  {tip}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Common Mistakes */}
                      {step.common_mistakes && step.common_mistakes.length > 0 && (
                        <div className="rounded-xl border-2 border-red-200/60 p-5 bg-gradient-to-br from-red-50/50 to-white shadow-sm">
                          <h4 className={`${inter.className} text-sm font-bold mb-4 flex items-center gap-2 text-[#0E1B2E]`}>
                            <AlertTriangle className="w-4 h-4 text-red-600" />
                            Common Mistakes
                          </h4>
                          <div className="space-y-3">
                            {step.common_mistakes.map((mistake: string, i: number) => (
                              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white border-2 border-red-100">
                                <div className="w-6 h-6 mt-0.5 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                                  <AlertTriangle className="w-3 h-3 text-red-600" />
                                </div>
                                <p className={`${inter.className} text-sm leading-relaxed text-slate-700`}>
                                  {mistake}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>

                  {/* Navigation */}
                  <div className="px-6 py-5 border-t-2 flex-shrink-0 flex items-center justify-between bg-gradient-to-r from-slate-50 to-white border-slate-200">
                    <button
                      onClick={() => setActiveStepMap((p) => ({
                        ...p,
                        [task.question_number]: Math.max(0, idx - 1),
                      }))}
                      disabled={idx === 0}
                      className={`${inter.className} px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
                        idx === 0
                          ? 'bg-slate-100 text-slate-400 cursor-not-allowed border-2 border-slate-200' 
                          : 'bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg border-2 border-transparent'
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
                          className={`h-2 rounded-full transition-all ${
                            i === idx
                              ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-600 w-10 shadow-md'
                              : i < idx
                              ? 'bg-blue-400 w-2'
                              : 'bg-slate-300 hover:bg-slate-400 w-2'
                          }`}
                        />
                      ))}
                    </div>

                    {idx === total - 1 ? (
                      !isCompleted ? (
                        <button
                          onClick={() => markTaskComplete(task.question_number)}
                          className={`${inter.className} px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white text-sm font-semibold hover:shadow-lg transition-all border-2 border-transparent`}
                        >
                          Mark Complete
                        </button>
                      ) : (
                        <div className={`${inter.className} px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 bg-green-50 text-green-700 border-2 border-green-200 shadow-sm`}>
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
                        className={`${inter.className} px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white text-sm font-semibold hover:shadow-lg transition-all flex items-center gap-2 border-2 border-transparent`}
                      >
                        Next Step
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border-2 border-slate-200 p-12 text-center flex flex-col items-center justify-center bg-white/60 backdrop-blur-sm">
                  <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
                    <Shield className="w-8 h-8 text-slate-400" />
                  </div>
                  <p className={`${inter.className} text-lg font-semibold text-slate-600`}>
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