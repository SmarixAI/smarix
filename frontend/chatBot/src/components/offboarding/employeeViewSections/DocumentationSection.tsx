'use client';

import { useEffect, useState, useMemo } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, FileText, Clock, Brain, HelpCircle, ExternalLink, Filter } from 'lucide-react';
import Loader from '../Loader';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

/* ================= TYPES ================= */

type Task = {
  id: string;
  title?: string;
  description?: string;
  priority: 'High' | 'Medium' | 'Low';
  tags: string[];
  source: 'AI' | 'Manager';
  reference?: string;
  questions?: string[];
  estimated_time_minutes?: number;
  knowledge_capture_method?: string;
  ai_analyzed?: boolean;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= PRIORITY STYLES ================= */

const getPriorityStyles = (priority: Task['priority']): string => {
  return priority === 'High'
    ? 'bg-red-50 text-red-700 border-2 border-red-300'
    : priority === 'Medium'
    ? 'bg-amber-50 text-amber-800 border-2 border-amber-300'
    : 'bg-green-50 text-green-700 border-2 border-green-300';
};

/* ================= COMPONENT ================= */

export default function EmployeeDocumentationSection({ employeeId, darkMode = false }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [acknowledged, setAcknowledged] = useState(false);
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(new Set());
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());

  // Filter state
  const [filterOpen, setFilterOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'high' | 'medium' | 'low' | 'ai' | 'manager'>('all');

  // Filter tasks based on active filter
  const filteredTasks = tasks.filter(task => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'high') return task.priority === 'High';
    if (activeFilter === 'medium') return task.priority === 'Medium';
    if (activeFilter === 'low') return task.priority === 'Low';
    if (activeFilter === 'ai') return task.source === 'AI';
    if (activeFilter === 'manager') return task.source === 'Manager';
    return true;
  });

  /* ================= LOAD TASKS ================= */

  useEffect(() => {
    setLoading(true);
    const fetchData = async () => {
      try {
        const response = await fetch('/api/offboarding/tasks');
        if (!response.ok) {
          console.error('Failed to fetch tasks data');
          setLoading(false);
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) {
          setLoading(false);
          return;
        }

        const employee =
          data.employees.find((e: any) => 
            e.employeeId === employeeId || 
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
          ) ?? data.employees[0];
        
        const allTasks = (employee.tasks?.ai ?? []).map((task: any) => ({
          ...task,
          tags: task.tags || ['Manual']
        }));
        
        const docTasks = allTasks.filter((task: Task) => task.id.startsWith('DOC'));
        setTasks(docTasks);
        setCompletedTaskIds(new Set());
        setExpandedTaskIds(new Set());
      } catch (error) {
        console.error('Error fetching documentation tasks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  const toggleTaskDetails = (taskId: string) => {
    setExpandedTaskIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const getTaskTitle = (task: Task): string => {
    if (task.title) return task.title;
    if (!task.description) return 'Untitled Task';
    
    let cleanTitle = task.description
      .replace(/\*\*/g, '')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\n/g, ' ')
      .trim();
    
    cleanTitle = cleanTitle
      .replace(/^Task Description[:\s]+(?:for|Knowledge Transfer[:\s]+)?/i, '')
      .replace(/^Documentation requirements:\s*/i, '')
      .trim();
    
    const firstPhrase = cleanTitle.split(/[.:\n]/)[0].trim();
    if (firstPhrase && firstPhrase.length > 0 && firstPhrase.length < 60) {
      return firstPhrase;
    }
    
    return cleanTitle.length > 60 ? cleanTitle.substring(0, 60) + '...' : cleanTitle;
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={false} message="Loading documents..." size="md" />;
  }

  return (
    <div className="h-full flex flex-col mt-2 gap-4">
      {/* ================= DOCUMENTATION TASK LIST ================= */}
      <div className="flex-1 rounded-2xl border-2 border-slate-200 shadow-lg bg-white/70 backdrop-blur-sm flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-5 border-b-2 border-slate-200 bg-gradient-to-r from-slate-50/80 to-blue-50/40">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h2 className={`${inter.className} text-xl font-bold text-[#0E1B2E]`}>Documentation Tasks</h2>
              <p className={`${inter.className} text-sm text-slate-600 mt-1`}>
                Documents you must complete before your last working day
              </p>
            </div>
            
            <div className="relative">
              <button
                onClick={() => setFilterOpen(!filterOpen)}
                className={`${inter.className} flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 transition-all text-sm font-semibold text-[#0E1B2E] shadow-sm`}
              >
                <Filter className="w-4 h-4" />
                <span>
                  {activeFilter === 'all' && 'All'}
                  {activeFilter === 'high' && 'High Priority'}
                  {activeFilter === 'medium' && 'Medium Priority'}
                  {activeFilter === 'low' && 'Low Priority'}
                  {activeFilter === 'ai' && 'AI Tasks'}
                  {activeFilter === 'manager' && 'Manager Tasks'}
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${filterOpen ? 'rotate-180' : ''}`} />
              </button>

              {filterOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border-2 border-slate-200 bg-white shadow-xl z-10 overflow-hidden">
                  <div className="py-1">
                    {[
                      { value: 'all', label: 'All Tasks' },
                      { value: 'high', label: 'High Priority' },
                      { value: 'medium', label: 'Medium Priority' },
                      { value: 'low', label: 'Low Priority' },
                      { value: 'ai', label: 'AI Tasks' },
                      { value: 'manager', label: 'Manager Tasks' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => {
                          setActiveFilter(option.value as any);
                          setFilterOpen(false);
                        }}
                        className={`${inter.className} w-full text-left px-4 py-2.5 text-sm font-medium transition-colors ${
                          activeFilter === option.value
                            ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white'
                            : 'text-[#0E1B2E] hover:bg-slate-50'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-y-auto divide-y-2 divide-slate-200">
          {filteredTasks.length === 0 ? (
            <div className="flex items-center justify-center h-full p-8">
              <p className={`${inter.className} text-slate-600`}>
                {tasks.length === 0 ? 'No tasks available' : 'No tasks match the selected filter'}
              </p>
            </div>
          ) : (
            filteredTasks.map(task => {
            const isDone = completedTaskIds.has(task.id);
            const isExpanded = expandedTaskIds.has(task.id);
            const hasDetails = task.description || task.questions?.length || task.reference || task.estimated_time_minutes || task.knowledge_capture_method;

            return (
              <div
                key={task.id}
                className={`${isDone ? 'opacity-60' : ''} transition-all duration-200`}
              >
                <div 
                  className={`px-6 py-5 flex justify-between items-start gap-4 ${
                    hasDetails ? 'cursor-pointer hover:bg-slate-50/50 transition-colors' : ''
                  }`}
                  onClick={() => hasDetails && toggleTaskDetails(task.id)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-3">
                      <h4 className={`${inter.className} font-bold text-base flex-1 text-[#0E1B2E]`}>
                        {getTaskTitle(task)}
                      </h4>
                      {task.ai_analyzed && (
                        <span className={`${inter.className} flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border-2 border-blue-200`}>
                          <Brain className="w-3.5 h-3.5" />
                          AI Analyzed
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-3">
                      <span className={`${jetbrainsMono.className} text-xs text-slate-600 bg-slate-100 px-2 py-1 rounded-md font-medium`}>
                        {task.source}
                      </span>
                      <span className="text-xs text-slate-400">•</span>
                      <span className={`${inter.className} text-xs text-slate-600`}>
                        {(task.tags || ['Manual']).join(', ')}
                      </span>
                      {task.estimated_time_minutes && (
                        <>
                          <span className="text-xs text-slate-400">•</span>
                          <span className={`${inter.className} flex items-center gap-1 text-xs text-slate-600`}>
                            <Clock className="w-3.5 h-3.5" />
                            ~{task.estimated_time_minutes} min
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className={`${inter.className} px-3 py-2 rounded-xl text-xs font-bold ${getPriorityStyles(task.priority)}`}>
                      {task.priority}
                    </span>

                    {hasDetails && (
                      <div className="p-2 rounded-lg transition text-slate-500" title={isExpanded ? "Collapse details" : "Expand details"}>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </div>
                    )}

                    {isDone ? (
                      <span className={`${inter.className} flex items-center gap-2 text-xs font-bold text-green-700`} onClick={(e) => e.stopPropagation()}>
                        <CheckCircle className="w-4 h-4" />
                        Completed
                      </span>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setCompletedTaskIds(prev => new Set(prev).add(task.id));
                        }}
                        className={`${inter.className} px-4 py-2.5 rounded-xl text-xs font-semibold text-white transition-all bg-gradient-to-r from-[#0E1B2E] to-blue-900 hover:shadow-lg`}
                      >
                        Mark as Done
                      </button>
                    )}
                  </div>
                </div>

                {isExpanded && hasDetails && (
                  <div className="px-6 pb-5 border-t-2 border-slate-200 bg-gradient-to-br from-slate-50/50 to-blue-50/30">
                    <div className="pt-5 space-y-5">
                      {task.description && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <FileText className="w-4 h-4 text-slate-600" />
                            <h4 className={`${inter.className} text-sm font-bold text-slate-800`}>
                              Full Description
                            </h4>
                          </div>
                          <div className={`${inter.className} text-sm ml-6 whitespace-pre-wrap text-slate-700 leading-relaxed`}>
                            {task.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
                          </div>
                        </div>
                      )}

                      {task.questions && task.questions.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <HelpCircle className="w-4 h-4 text-purple-600" />
                            <h4 className={`${inter.className} text-sm font-bold text-slate-800`}>
                              Key Questions to Address
                            </h4>
                          </div>
                          <ul className="space-y-2 ml-6">
                            {task.questions.map((question, idx) => (
                              <li key={idx} className={`${inter.className} text-sm text-slate-700 flex items-start gap-2`}>
                                <span className="text-purple-600 font-bold mt-0.5">•</span>
                                <span>{question}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {task.reference && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <FileText className="w-4 h-4 text-blue-600" />
                            <h4 className={`${inter.className} text-sm font-bold text-slate-800`}>
                              Related Files
                            </h4>
                          </div>
                          <div className={`${jetbrainsMono.className} text-xs text-slate-600 ml-6 space-y-2`}>
                            {task.reference.split(', ').map((ref, idx) => (
                              <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
                                <ExternalLink className="w-3.5 h-3.5 text-blue-600" />
                                <span>{ref.trim()}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {task.knowledge_capture_method && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <Clock className="w-4 h-4 text-amber-600" />
                            <h4 className={`${inter.className} text-sm font-bold text-slate-800`}>
                              Knowledge Capture Method
                            </h4>
                          </div>
                          <div className={`${inter.className} text-sm ml-6 text-slate-700`}>
                            {task.knowledge_capture_method.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
          )}
        </div>
      </div>

      {/* ================= ACKNOWLEDGEMENT ================= */}
      <div className="rounded-2xl border-2 border-slate-200 bg-white/70 backdrop-blur-sm p-5 flex items-center justify-between shadow-md">
        <div>
          <h3 className={`${inter.className} font-bold text-[#0E1B2E]`}>
            Final Acknowledgement
          </h3>
          <p className={`${inter.className} text-xs mt-1 text-slate-600`}>
            Confirm that you will complete all required documentation
          </p>
        </div>

        <button
          disabled={acknowledged}
          onClick={() => setAcknowledged(true)}
          className={`${inter.className} flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            acknowledged
              ? 'bg-green-600 text-white shadow-sm'
              : 'bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          {acknowledged ? 'Acknowledged' : 'I Acknowledge'}
        </button>
      </div>
    </div>
  );
}