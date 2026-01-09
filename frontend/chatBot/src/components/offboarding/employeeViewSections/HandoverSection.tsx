'use client';

import { useEffect, useState, useMemo } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, FileText, Clock, Brain, HelpCircle, ExternalLink, User, Filter } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type Task = {
  id: string;
  title?: string;  // Short title (AI-generated)
  description?: string;  // Full description
  priority: 'High' | 'Medium' | 'Low';
  tags: string[];
  source: 'AI' | 'Manager';
  reference?: string;
  questions?: string[];
  estimated_time_minutes?: number;
  knowledge_capture_method?: string;
  ai_analyzed?: boolean;
  suggested_recipient?: string;
  suggested_recipient_reason?: string;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= PRIORITY STYLES ================= */

const getPriorityStyles = (priority: Task['priority'], darkMode: boolean): string => {
  if (darkMode) {
    return priority === 'High'
      ? 'bg-red-900/30 text-red-300 border-red-700'
      : priority === 'Medium'
      ? 'bg-yellow-900/30 text-yellow-300 border-yellow-700'
      : 'bg-green-900/30 text-green-300 border-green-700';
  }
  return priority === 'High'
    ? 'bg-red-50 text-red-700 border-red-300'
    : priority === 'Medium'
    ? 'bg-yellow-50 text-yellow-800 border-yellow-300'
    : 'bg-green-50 text-green-700 border-green-300';
};

/* ================= COMPONENT ================= */

export default function EmployeeHandoverSection({ employeeId, darkMode = false }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [acknowledged, setAcknowledged] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
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

  /* ================= LOAD HANDOVER TASKS ================= */

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
          console.log('No employees found in tasks data');
          setLoading(false);
          return;
        }

        console.log('Handovers - Looking for employeeId:', employeeId);
        console.log('Handovers - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        const employee =
          data.employees.find((e: any) => 
            e.employeeId === employeeId || 
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
          ) ?? data.employees[0];
        
        console.log('Handovers - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');

        // Filter for handover tasks (IDs starting with "HO")
        const allTasks = (employee.tasks?.ai ?? []).map((task: any) => ({
          ...task,
          tags: task.tags || ['Manual']
        }));
        
        const handoverTasks = allTasks.filter((task: Task) => task.id.startsWith('HO'));
        setTasks(handoverTasks);
        setCompletedTaskIds(new Set());
        setExpandedTaskIds(new Set());
      } catch (error) {
        console.error('Error fetching handover tasks data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY ================= */

  const summary = useMemo(() => {
    const total = tasks.length;
    const completed = completedTaskIds.size;
    const pending = total - completed;

    return { total, completed, pending };
  }, [tasks, completedTaskIds]);

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

  // Helper to get title - use title field if available, otherwise extract from description
  const getTaskTitle = (task: Task): string => {
    // Use the title field if it exists (AI-generated short title)
    if (task.title) {
      return task.title;
    }
    
    // Fallback: extract from description if title not available
    if (!task.description) return 'Untitled Task';
    
    // Remove markdown formatting
    let cleanTitle = task.description
      .replace(/\*\*/g, '')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\n/g, ' ')
      .trim();
    
    // Remove common prefixes
    cleanTitle = cleanTitle
      .replace(/^Task Description[:\s]+(?:for|Knowledge Transfer[:\s]+)?/i, '')
      .replace(/^Handover session:\s*/i, '')
      .replace(/^Documentation requirements:\s*/i, '')
      .trim();
    
    // Extract first meaningful phrase (before first period, colon, or newline)
    const firstPhrase = cleanTitle.split(/[.:\n]/)[0].trim();
    if (firstPhrase && firstPhrase.length > 0 && firstPhrase.length < 60) {
      return firstPhrase;
    }
    
    // Fallback: first 60 characters
    return cleanTitle.length > 60 ? cleanTitle.substring(0, 60) + '...' : cleanTitle;
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={false} message="Loading handovers..." size="md" />;
  }

  return (
    <div className="h-full flex flex-col">
      {/* ================= HANDOVER TASK LIST (Scrollable) ================= */}
      <div className="flex-1 rounded-lg border border-gray-200 shadow-sm bg-white flex flex-col overflow-hidden">
        {/* Enhanced Header with Filter */}
        <div className="px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-[#0E1B2E]/5 to-[#0E1B2E]/10">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h2 className="text-lg font-bold text-[#0E1B2E]">Handover Tasks</h2>
              <p className="text-xs text-[#0E1B2E]/60 mt-1">
                Items you must transfer before your last working day
              </p>
            </div>
            
            {/* Filter Dropdown */}
            <div className="relative">
              <button
                onClick={() => setFilterOpen(!filterOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-[#0E1B2E]/5 transition-colors text-sm font-medium text-[#0E1B2E]"
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

              {/* Dropdown Menu */}
              {filterOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 rounded-lg border border-gray-200 bg-white shadow-lg z-10">
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
                        className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                          activeFilter === option.value
                            ? 'bg-[#0E1B2E] text-white'
                            : 'text-[#0E1B2E] hover:bg-[#0E1B2E]/5'
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

        <div className="flex-1 overflow-y-auto divide-y divide-gray-200">
          {filteredTasks.length === 0 ? (
            <div className="flex items-center justify-center h-full p-8">
              <p className="text-[#0E1B2E]/60">
                {tasks.length === 0 ? 'No tasks available' : 'No tasks match the selected filter'}
              </p>
            </div>
          ) : (
            filteredTasks.map(task => {
            const isDone = completedTaskIds.has(task.id);
            const isExpanded = expandedTaskIds.has(task.id);
            const hasDetails = task.description || task.questions?.length || task.reference || task.estimated_time_minutes || task.knowledge_capture_method || task.suggested_recipient;

            return (
              <div
                key={task.id}
                className={`
                  ${isDone ? 'opacity-60' : ''}
                  transition-all duration-200
                `}
              >
                {/* MAIN TASK ROW */}
                <div 
                  className={`px-5 py-4 flex justify-between items-start gap-4 ${
                    hasDetails ? 'cursor-pointer hover:bg-[#0E1B2E]/5 transition-colors' : ''
                  }`}
                  onClick={() => hasDetails && toggleTaskDetails(task.id)}
                >
                  {/* LEFT */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2">
                      <h4 className="font-bold text-base flex-1 text-[#0E1B2E]">
                        {getTaskTitle(task)}
                      </h4>
                      {task.ai_analyzed && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/20">
                          <Brain className="w-3 h-3" />
                          AI Analyzed
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <span className={`text-xs ${
                        darkMode ? "text-gray-400" : "text-slate-600"
                      }`}>
                        Source: {task.source}
                      </span>
                      <span className={`text-xs ${
                        darkMode ? "text-gray-500" : "text-slate-500"
                      }`}>•</span>
                      <span className={`text-xs ${
                        darkMode ? "text-gray-400" : "text-slate-600"
                      }`}>
                        Tags: {(task.tags || ['Manual']).join(', ')}
                      </span>
                      {task.estimated_time_minutes && (
                        <>
                          <span className={`text-xs ${
                            darkMode ? "text-gray-500" : "text-slate-500"
                          }`}>•</span>
                          <span className={`flex items-center gap-1 text-xs ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}>
                            <Clock className="w-3 h-3" />
                            ~{task.estimated_time_minutes} min
                          </span>
                        </>
                      )}
                      {task.suggested_recipient && (
                        <>
                          <span className={`text-xs ${
                            darkMode ? "text-gray-500" : "text-slate-500"
                          }`}>•</span>
                          <span className={`flex items-center gap-1 text-xs ${
                            darkMode ? "text-[#0E1B2E]/60" : "text-[#0E1B2E]"
                          }`}>
                            <User className="w-3 h-3" />
                            To: {task.suggested_recipient}
                  </span>
                        </>
                      )}
                    </div>
              </div>

                  {/* RIGHT */}
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {/* PRIORITY */}
              <span
                      className={`
                        px-3 py-1.5 rounded-lg text-xs font-semibold border
                        ${getPriorityStyles(task.priority, darkMode)}
                      `}
              >
                      {task.priority}
              </span>

                    {/* EXPAND BUTTON */}
                    {hasDetails && (
                      <div
                        className={`p-1.5 rounded-lg transition ${
                          darkMode
                            ? "text-gray-400"
                            : "text-slate-500"
                        }`}
                        title={isExpanded ? "Collapse details" : "Expand details"}
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
            </div>
                    )}

                    {/* ACTION */}
                    {isDone ? (
                <span
                        className={`flex items-center gap-1.5 text-xs font-semibold ${
                          darkMode ? "text-green-400" : "text-green-700"
                        }`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <CheckCircle className="w-4 h-4" />
                        Completed
                </span>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setCompletedTaskIds(prev => new Set(prev).add(task.id));
                        }}
                        className={`
                          px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition
                          ${darkMode
                            ? "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
                            : "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
                          }
                        `}
                      >
                        Mark as Done
                      </button>
                    )}
                  </div>
              </div>

                {/* EXPANDED DETAILS */}
                {isExpanded && hasDetails && (
                  <div className={`px-5 pb-4 border-t ${
                    darkMode ? "border-gray-700 bg-gray-800/50" : "border-slate-200 bg-slate-50"
                  }`}>
                    <div className="pt-4 space-y-4">
                      {/* FULL DESCRIPTION (in expanded view) */}
                      {task.description && (
              <div>
                          <div className="flex items-center gap-2 mb-2">
                            <FileText className={`w-4 h-4 ${
                              darkMode ? "text-gray-400" : "text-slate-600"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-gray-200" : "text-slate-800"
                            }`}>
                              Full Description
                            </h4>
                          </div>
                          <div className={`text-sm ml-6 whitespace-pre-wrap ${
                            darkMode ? "text-gray-300" : "text-slate-700"
                          }`}>
                            {task.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
                          </div>
              </div>
                      )}

                      {/* SUGGESTED RECIPIENT (highlighted for handover) */}
                      {task.suggested_recipient && (
                        <div className={`p-3 rounded-lg ${
                          darkMode ? "bg-[#0E1B2E]/20 border border-[#0E1B2E]/70" : "bg-[#0E1B2E]/5 border border-[#0E1B2E]/20"
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            <User className={`w-4 h-4 ${
                              darkMode ? "text-[#0E1B2E]/60" : "text-[#0E1B2E]"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-[#0E1B2E]/80" : "text-[#0E1B2E]"
                            }`}>
                              Suggested Handover Recipient
                            </h4>
                          </div>
                          <div className={`text-sm ml-6 ${
                            darkMode ? "text-[#0E1B2E]/70" : "text-[#0E1B2E]/90"
                          }`}>
                            <span className="font-semibold">{task.suggested_recipient}</span>
                            {task.suggested_recipient_reason && (
                              <span className={`ml-2 text-xs ${
                                darkMode ? "text-[#0E1B2E]/60" : "text-[#0E1B2E]"
                              }`}>
                                ({task.suggested_recipient_reason})
                              </span>
                            )}
              </div>
            </div>
                      )}

                      {/* QUESTIONS */}
                      {task.questions && task.questions.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <HelpCircle className={`w-4 h-4 ${
                              darkMode ? "text-[#0E1B2E]/60" : "text-[#0E1B2E]"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-gray-200" : "text-slate-800"
                            }`}>
                              Key Questions to Address
                            </h4>
                          </div>
                          <ul className="space-y-2 ml-6">
                            {task.questions.map((question, idx) => (
                              <li key={idx} className={`text-sm ${
                                darkMode ? "text-gray-300" : "text-slate-700"
                              }`}>
                                <span className="mr-2">•</span>
                                {question}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* REFERENCE FILES */}
                      {task.reference && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <FileText className={`w-4 h-4 ${
                              darkMode ? "text-blue-400" : "text-blue-600"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-gray-200" : "text-slate-800"
                            }`}>
                              Related Files
                            </h4>
            </div>
                          <div className={`text-xs ${
                            darkMode ? "text-gray-400" : "text-slate-600"
                          } ml-6`}>
                            {task.reference.split(', ').map((ref, idx) => (
                              <div key={idx} className="flex items-center gap-1 mb-1">
                                <ExternalLink className="w-3 h-3" />
                                <span className="font-mono">{ref.trim()}</span>
          </div>
        ))}
                          </div>
                        </div>
                      )}

                      {/* KNOWLEDGE CAPTURE METHOD */}
                      {task.knowledge_capture_method && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Clock className={`w-4 h-4 ${
                              darkMode ? "text-purple-400" : "text-purple-600"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-gray-200" : "text-slate-800"
                            }`}>
                              Knowledge Capture Method
                            </h4>
                          </div>
                          <div className={`text-sm ml-6 ${
                            darkMode ? "text-gray-300" : "text-slate-700"
                          }`}>
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
    </div>
  );
}

/* ================= HELPERS ================= */

function SummaryCard({
  label,
  value,
  tone = 'slate',
  darkMode = false
}: {
  label: string;
  value: number;
  tone?: 'green' | 'yellow' | 'slate';
  darkMode?: boolean;
}) {
  const getTones = (tone: string, darkMode: boolean): string => {
    if (darkMode) {
      return tone === 'green'
        ? 'bg-green-900/30 text-green-300'
        : tone === 'yellow'
        ? 'bg-yellow-900/30 text-yellow-300'
        : 'bg-gray-800 text-gray-100';
    }
    return tone === 'green'
      ? 'bg-green-50 text-green-800'
      : tone === 'yellow'
      ? 'bg-yellow-50 text-yellow-800'
      : 'bg-slate-50 text-slate-900';
  };

  return (
    <div className={`rounded-xl border px-4 py-3 transition-colors duration-300 ${
      darkMode ? "border-gray-700" : ""
    } ${getTones(tone, darkMode)}`}>
      <p className="text-xs">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
