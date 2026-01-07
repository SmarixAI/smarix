'use client';

import { useEffect, useState, useMemo } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, FileText, Clock, Brain, HelpCircle, ExternalLink, User } from 'lucide-react';
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
    return <Loader darkMode={darkMode} message="Loading handovers..." size="md" />;
  }

  return (
    <div className="space-y-8">

      {/* ================= SUMMARY ================= */}
      <div className={`rounded-2xl border shadow-sm transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800"
          : "border-slate-200 bg-white"
      }`}>
        <div className={`px-5 py-4 border-b ${
          darkMode ? "border-gray-700" : ""
        }`}>
          <h3 className={`font-semibold ${
            darkMode ? "text-gray-100" : "text-slate-900"
          }`}>
            Your Handover Responsibilities
          </h3>
          <p className={`text-xs mt-1 ${
            darkMode ? "text-gray-400" : "text-slate-600"
          }`}>
            Items you must transfer before your last working day
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 px-5 py-4">
          <SummaryCard label="Total Items" value={summary.total} darkMode={darkMode} />
          <SummaryCard label="Completed" value={summary.completed} tone="green" darkMode={darkMode} />
          <SummaryCard label="Pending" value={summary.pending} tone="yellow" darkMode={darkMode} />
        </div>
      </div>

      {/* ================= HANDOVER TASK LIST ================= */}
      <div className={`rounded-2xl border shadow-sm transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800"
          : "border-slate-200 bg-white"
      }`}>
        <div className={`px-5 py-4 border-b ${
          darkMode ? "border-gray-700" : ""
        }`}>
          <h3 className={`font-semibold ${
            darkMode ? "text-gray-100" : "text-slate-900"
          }`}>
            Handover Sessions
          </h3>
        </div>

        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {tasks.map(task => {
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
                    hasDetails ? 'cursor-pointer hover:bg-opacity-50 transition-colors' : ''
                  } ${darkMode ? hasDetails ? 'hover:bg-gray-700/30' : '' : hasDetails ? 'hover:bg-slate-50' : ''}`}
                  onClick={() => hasDetails && toggleTaskDetails(task.id)}
                >
                  {/* LEFT */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2">
                      <h4 className={`font-bold text-base flex-1 ${
                        darkMode ? "text-gray-50" : "text-slate-900"
                      }`}>
                        {getTaskTitle(task)}
                      </h4>
                      {task.ai_analyzed && (
                        <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
                          darkMode 
                            ? "bg-indigo-900/30 text-indigo-300 border border-indigo-700"
                            : "bg-indigo-50 text-indigo-700 border border-indigo-300"
                        }`}>
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
                            darkMode ? "text-indigo-400" : "text-indigo-600"
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
                            ? "bg-indigo-600 hover:bg-indigo-700"
                            : "bg-indigo-600 hover:bg-indigo-700"
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
                          darkMode ? "bg-indigo-900/20 border border-indigo-700" : "bg-indigo-50 border border-indigo-200"
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            <User className={`w-4 h-4 ${
                              darkMode ? "text-indigo-400" : "text-indigo-600"
                            }`} />
                            <h4 className={`text-sm font-semibold ${
                              darkMode ? "text-indigo-200" : "text-indigo-900"
                            }`}>
                              Suggested Handover Recipient
                            </h4>
                          </div>
                          <div className={`text-sm ml-6 ${
                            darkMode ? "text-indigo-300" : "text-indigo-700"
                          }`}>
                            <span className="font-semibold">{task.suggested_recipient}</span>
                            {task.suggested_recipient_reason && (
                              <span className={`ml-2 text-xs ${
                                darkMode ? "text-indigo-400" : "text-indigo-600"
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
                              darkMode ? "text-indigo-400" : "text-indigo-600"
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
          })}
        </div>

        {tasks.length === 0 && (
          <div className={`px-5 py-8 text-sm italic text-center ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            No handover tasks assigned to you.
          </div>
        )}
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
