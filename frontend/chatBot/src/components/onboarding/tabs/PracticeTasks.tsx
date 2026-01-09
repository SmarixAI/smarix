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
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface PracticeTasksProps {
  tasks?: any[];
  openTask?: number | null;
  onSelectTask?: (n: number | null) => void;
  employeeId?: string | null;
  activeRepos?: string[];
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
}

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
      <div className="p-8 text-center min-h-[300px] flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
        <Shield className="w-12 h-12 text-gray-400 mb-4" />
        <p className="text-xl font-semibold mb-1 text-gray-900">
          No task selected
        </p>
        <p className="text-sm text-gray-600">
          Select a task from the sidebar
        </p>
      </div>
    );
  }

  return (
    <div className="w-full p-2 lg:p-4 bg-[#FAFAFA] relative">
      {/* Grid Pattern Background for practice section */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      <div className="relative z-10 space-y-3 lg:space-y-4">
        {filteredTasks.map((task: any) => {
          const isCompleted = practicedMap[task.question_number];
          const idx = activeStepMap[task.question_number] ?? 0;
          const total = task.steps?.length || 1;
          const step = task.steps?.[idx];
          const key = `${task.question_number}-${step?.step_number || 1}`;

          return (
            <div key={task.question_number} className="space-y-3 lg:space-y-4">
              {/* TASK OVERVIEW */}
              <div className="rounded-lg border border-gray-200 p-4 flex-shrink-0 bg-white">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-base font-semibold text-gray-900">
                    {task.title || `Task #${task.question_number}`}
                  </h3>
                  {isCompleted && (
                    <div className="px-2 py-1 rounded-full text-xs font-semibold flex items-center gap-1 bg-green-50 text-green-700 border border-green-200">
                      <Check className="w-3 h-3" />
                      Completed
                    </div>
                  )}
                </div>
                <p className="text-sm leading-relaxed line-clamp-2 text-gray-600">
                  {task.question_description || 'Android Development Practice'}
                </p>
              </div>

              {/* STEPS CONTAINER */}
              {task.steps && task.steps.length > 0 ? (
                <div className="rounded-lg border border-gray-200 bg-white">
                  {/* Progress Header */}
                  <div className="px-5 py-4 border-b bg-gray-50 border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-800 text-white">
                          <span className="font-semibold text-lg">{idx + 1}</span>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            Step {idx + 1} of {total}
                          </p>
                          <p className="text-xs text-gray-600">
                            {step.step_title}
                          </p>
                        </div>
                      </div>
                      <span className="text-sm font-semibold px-3 py-1 rounded-full bg-gray-100 text-gray-700 border border-gray-200">
                        {Math.round(((idx + 1) / total) * 100)}%
                      </span>
                    </div>
                    
                    <div className="flex space-x-1">
                      {Array.from({ length: total }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 flex-1 rounded-full transition-all duration-500 ${
                            i < idx + 1 
                              ? 'bg-gray-700' 
                              : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="px-5 py-5 space-y-4">
                      
                      {/* What to implement */}
                      <div className="rounded-lg border border-gray-200 p-4 bg-gray-50">
                        <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-900">
                          What to implement
                        </h4>
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown>
                            {step.implementation_details || 'No implementation details provided.'}
                          </ReactMarkdown>
                        </div>
                      </div>

                      {/* Enhanced Code Section */}
                      <div className={`rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-sm overflow-hidden group ${
                        expandedCode[key]
                          ? 'border-gray-300 bg-gray-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white hover:bg-gray-50'
                      }`} 
                        onClick={() => toggleCodeView(task.question_number, step.step_number)}
                      >
                        <div className={`px-4 py-3 border-b flex items-center justify-between transition-all ${
                          expandedCode[key] ? 'bg-gray-100 border-gray-200' : 'bg-white border-gray-200'
                        }`}>
                          <div className="flex items-center gap-2">
                            <Code className="w-4 h-4 text-gray-600" />
                            <span className="text-sm font-semibold text-gray-900">
                              {expandedCode[key] ? "Solution Code" : "View Solution Code"}
                            </span>
                          </div>
                          <ChevronRight className={`w-5 h-5 transition-transform duration-300 text-gray-600 ${
                            expandedCode[key] ? 'rotate-90' : ''
                          }`} />
                        </div>
                        
                        {expandedCode[key] && step.code_snippet && (
                          <div className="p-4 max-h-64 overflow-y-auto">
                            <SyntaxHighlighter
                              language="java"
                              style={oneLight}
                              customStyle={{
                                borderRadius: '0.5rem',
                                padding: '1.25rem !important',
                                fontSize: '0.875rem',
                                margin: '0 !important',
                                border: '1px solid #e5e7eb',
                                background: '#f9fafb',
                              }}
                            >
                              {step.code_snippet}
                            </SyntaxHighlighter>
                          </div>
                        )}
                      </div>

                      {/* Tips */}
                      {step.tips && step.tips.length > 0 && (
                        <div className="rounded-lg border border-gray-200 p-4 bg-gray-50">
                          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-900">
                            Tips
                          </h4>
                          <div className="space-y-2">
                            {step.tips.map((tip: string, i: number) => (
                              <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg bg-white border border-gray-200">
                                <div className="w-2 h-2 mt-2 rounded-full bg-gray-600 flex-shrink-0" />
                                <p className="text-sm leading-relaxed text-gray-700">
                                  {tip}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Common Mistakes */}
                      {step.common_mistakes && step.common_mistakes.length > 0 && (
                        <div className="rounded-lg border border-gray-200 p-4 bg-gray-50">
                          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-900">
                            Common Mistakes
                          </h4>
                          <div className="space-y-2">
                            {step.common_mistakes.map((mistake: string, i: number) => (
                              <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg bg-white border border-gray-200">
                                <div className="w-2 h-2 mt-2 rounded-full bg-gray-600 flex-shrink-0" />
                                <p className="text-sm leading-relaxed text-gray-700">
                                  {mistake}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>

                  {/* Navigation */}
                  <div className="px-5 py-4 border-t flex-shrink-0 flex items-center justify-between bg-white border-gray-200">
                    <button
                      onClick={() => setActiveStepMap((p) => ({
                        ...p,
                        [task.question_number]: Math.max(0, idx - 1),
                      }))}
                      disabled={idx === 0}
                      className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all ${
                        idx === 0
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                          : 'bg-gray-900 text-white hover:bg-gray-800'
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
                          className={`w-2 h-2 rounded-full transition-all ${
                            i === idx
                              ? 'bg-gray-700 w-8'
                              : i < idx
                              ? 'bg-gray-400'
                              : 'bg-gray-300 hover:bg-gray-400'
                          }`}
                        />
                      ))}
                    </div>

                    {idx === total - 1 ? (
                      !isCompleted ? (
                        <button
                          onClick={() => markTaskComplete(task.question_number)}
                          className="px-6 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-all"
                        >
                          Mark Complete
                        </button>
                      ) : (
                        <div className="px-6 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 bg-green-50 text-green-700 border border-green-200">
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
                        className="px-6 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-all flex items-center gap-1"
                      >
                        Next Step
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-gray-200 p-8 text-center flex flex-col items-center justify-center bg-gray-50">
                  <Shield className="w-12 h-12 opacity-40 mb-4 text-gray-400" />
                  <p className="text-lg font-medium text-gray-600">
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
