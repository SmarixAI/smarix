'use client';

import { useEffect, useState } from 'react';
import { UserPlus, XCircle, ChevronDown, ChevronUp, FileText, HelpCircle, ExternalLink, Clock } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type Task = {
  id: string;
  title: string;
  priority: 'High' | 'Medium' | 'Low';
  tags: string[];
  source: 'AI' | 'Manager';
  status?: 'active' | 'inactive' | 'not_needed';
  description?: string;
  questions?: string[];
  reference?: string;
  estimated_time_minutes?: number;
  knowledge_capture_method?: string;
};

type FinalCallSectionProps = {
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

export default function FinalCallSection({
  employeeId,
  darkMode = false
}: FinalCallSectionProps) {
  const [aiTasks, setAiTasks] = useState<Task[]>([]);
  const [managerTasks, setManagerTasks] = useState<Task[]>([]);
  const [updateCounter, setUpdateCounter] = useState(0); // Force re-render
  const [employeeStatus, setEmployeeStatus] = useState<string>('active');
  const [loading, setLoading] = useState(true);

  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newPriority, setNewPriority] =
    useState<'High' | 'Medium' | 'Low'>('Medium');

  // Filter states
  const [priorityFilter, setPriorityFilter] = useState<'All' | 'High' | 'Medium' | 'Low'>('All');
  const [showNotNeeded, setShowNotNeeded] = useState(false);
  
  // Expanded task IDs
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(new Set());

    /* ================= SUMMARY DERIVED DATA ================= */

const allTasks = [...aiTasks, ...managerTasks];
const activeTasks = allTasks.filter(t => t.status !== 'not_needed');

const summary = {
  total: activeTasks.length,
  high: activeTasks.filter(t => t.priority === 'High').length,
  medium: activeTasks.filter(t => t.priority === 'Medium').length,
  low: activeTasks.filter(t => t.priority === 'Low').length,
  notNeeded: allTasks.filter(t => t.status === 'not_needed').length,
  completed: 0,
  remaining: activeTasks.length,
  yetToAssign: activeTasks.length
};

// Filter tasks based on selected filters
const filteredAiTasks = aiTasks.filter(task => {
  // If "Show Not Needed" is checked, only show not_needed tasks
  // If "Show Not Needed" is unchecked, only show active tasks (not not_needed)
  if (showNotNeeded) {
    if (task.status !== 'not_needed') return false;
  } else {
    if (task.status === 'not_needed') return false;
  }
  // Apply priority filter
  if (priorityFilter !== 'All' && task.priority !== priorityFilter) return false;
  return true;
});

const filteredManagerTasks = managerTasks.filter(task => {
  // If "Show Not Needed" is checked, only show not_needed tasks
  // If "Show Not Needed" is unchecked, only show active tasks (not not_needed)
  if (showNotNeeded) {
    if (task.status !== 'not_needed') return false;
  } else {
    if (task.status === 'not_needed') return false;
  }
  // Apply priority filter
  if (priorityFilter !== 'All' && task.priority !== priorityFilter) return false;
  return true;
});


  /* ================= LOAD TASKS ================= */

  useEffect(() => {
    // Clear state when employeeId changes to prevent stale data
    setAiTasks([]);
    setManagerTasks([]);
    setUpdateCounter(0); // Reset update counter
    setLoading(true);

    const fetchData = async () => {
      try {
        // Fetch employee status
        const empResponse = await fetch('/api/offboarding/employees');
        if (empResponse.ok) {
          const empData = await empResponse.json();
          const employee = empData.employees?.find((e: any) => e.employeeId === employeeId);
          if (employee) {
            setEmployeeStatus(employee.status || 'active');
          }
        }

        const response = await fetch('/api/offboarding/tasks');
        if (!response.ok) {
          console.error('Failed to fetch tasks data');
          setLoading(false);
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) {
          console.log('Manager FinalCall - No employees found in tasks data');
          setLoading(false);
          return;
        }

        console.log('Manager FinalCall - Looking for employeeId:', employeeId);
        console.log('Manager FinalCall - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        let employee = data.employees.find((e: any) => 
          e.employeeId === employeeId || 
          e.employee_id === employeeId ||
          String(e.employeeId) === String(employeeId) ||
          String(e.employee_id) === String(employeeId)
        );

        if (!employee) {
          console.log('Manager FinalCall - Employee not found, using first employee');
          employee = data.employees[0];
        }

        console.log('Manager FinalCall - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Manager FinalCall - Employee tasks:', employee?.tasks);

        // Set state if employee found (removed strict check to allow fallback)
        if (employee) {
          // Get current employee status (already fetched above)
          // Mark tasks as not needed if employee status is "inactive" (not "active" or "leaving")
          // The user said: "if status is active is inactive then it means its not needed"
          // So if status is NOT "active" (i.e., "inactive"), mark as not needed
          const isInactive = employeeStatus === 'inactive' || (employeeStatus !== 'active' && employeeStatus !== 'leaving');
          
          // Remove duplicates by creating a Map with id as key
          const aiTasksMap = new Map<string, Task>();
          (employee.tasks?.ai ?? []).forEach((task: any) => {
            if (!aiTasksMap.has(task.id)) {
              aiTasksMap.set(task.id, {
                ...task,
                tags: task.tags || ['Manual'],
                // Only set status to not_needed if employee is inactive AND task doesn't already have a status
                status: task.status || (isInactive ? 'not_needed' : 'active')
              });
            }
          });
          
          const managerTasksMap = new Map<string, Task>();
          (employee.tasks?.manager ?? []).forEach((task: any) => {
            if (!managerTasksMap.has(task.id)) {
              managerTasksMap.set(task.id, {
                ...task,
                tags: task.tags || ['Manual'],
                status: task.status || (isInactive ? 'not_needed' : 'active')
              });
            }
          });
          
          setAiTasks(Array.from(aiTasksMap.values()));
          setManagerTasks(Array.from(managerTasksMap.values()));
        } else {
          console.log('Manager FinalCall - No employee found, setting empty tasks');
          setAiTasks([]);
          setManagerTasks([]);
        }
      } catch (error) {
        console.error('Error fetching tasks data:', error);
        setAiTasks([]);
        setManagerTasks([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= ACTION HANDLERS ================= */

  const updatePriority = async (
    id: string,
    source: Task['source'],
    newPriority: Task['priority']
  ) => {
    // Store old priority for potential revert BEFORE updating
    const oldPriority = source === 'AI' 
      ? aiTasks.find(t => t.id === id)?.priority
      : managerTasks.find(t => t.id === id)?.priority;

    // Update local state immediately for better UX using functional form
    if (source === 'AI') {
      setAiTasks(prev => {
        const updated = prev.map(t =>
          t.id === id ? { ...t, priority: newPriority } : t
        );
        return updated;
      });
    } else {
      setManagerTasks(prev => {
        const updated = prev.map(t =>
          t.id === id ? { ...t, priority: newPriority } : t
        );
        return updated;
      });
    }
    // Force re-render
    setUpdateCounter(prev => prev + 1);

    try {
      // Update in backend
      const response = await fetch('/api/offboarding/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeId: employeeId,
          taskId: id,
          priority: newPriority,
          source: source === 'AI' ? 'ai' : 'manager',
        }),
      });

      if (!response.ok) {
        console.error('Failed to update task priority');
        // Revert on error using functional form
        if (oldPriority) {
          if (source === 'AI') {
            setAiTasks(prev => prev.map(t =>
              t.id === id ? { ...t, priority: oldPriority } : t
            ));
          } else {
            setManagerTasks(prev => prev.map(t =>
              t.id === id ? { ...t, priority: oldPriority } : t
            ));
          }
        }
      }
    } catch (error) {
      console.error('Error updating task priority:', error);
      // Revert on error using functional form
      if (oldPriority) {
        if (source === 'AI') {
          setAiTasks(prev => prev.map(t =>
            t.id === id ? { ...t, priority: oldPriority } : t
          ));
        } else {
          setManagerTasks(prev => prev.map(t =>
            t.id === id ? { ...t, priority: oldPriority } : t
          ));
        }
      }
    }
  };

  const markTaskAsNotNeeded = async (id: string, source: Task['source']) => {
    // Update local state immediately
    if (source === 'AI') {
      setAiTasks(prev => prev.map(t => 
        t.id === id ? { ...t, status: 'not_needed' as const } : t
      ));
    } else {
      setManagerTasks(prev => prev.map(t => 
        t.id === id ? { ...t, status: 'not_needed' as const } : t
      ));
    }
    setUpdateCounter(prev => prev + 1);

    // Update in backend
    try {
      const response = await fetch('/api/offboarding/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeId: employeeId,
          taskId: id,
          status: 'not_needed',
          source: source === 'AI' ? 'ai' : 'manager',
        }),
      });

      if (!response.ok) {
        console.error('Failed to mark task as not needed');
        // Revert on error
        if (source === 'AI') {
          setAiTasks(prev => prev.map(t => 
            t.id === id ? { ...t, status: 'active' as const } : t
          ));
        } else {
          setManagerTasks(prev => prev.map(t => 
            t.id === id ? { ...t, status: 'active' as const } : t
          ));
        }
      }
    } catch (error) {
      console.error('Error marking task as not needed:', error);
      // Revert on error
      if (source === 'AI') {
        setAiTasks(prev => prev.map(t => 
          t.id === id ? { ...t, status: 'active' as const } : t
        ));
      } else {
        setManagerTasks(prev => prev.map(t => 
          t.id === id ? { ...t, status: 'active' as const } : t
        ));
      }
    }
  };

  const assignHandover = (task: Task) => {
    console.log('Assign handover:', task.title);
  };

  const addManagerTask = async () => {
    if (!newTaskTitle.trim()) return;

    const taskTitle = newTaskTitle.trim();
    const taskPriority = newPriority;
    
    const tempId = crypto.randomUUID();
    const newTask = {
      id: tempId,
      title: taskTitle,
      priority: taskPriority,
      tags: ['Manual'],
      source: 'Manager' as const
    };

    // Update local state immediately
    setManagerTasks(prev => [...prev, newTask]);

    // Clear form
    setNewTaskTitle('');
    setNewPriority('Medium');

    // Save to backend
    try {
      const response = await fetch('/api/offboarding/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeId: employeeId,
          action: 'add',
          title: taskTitle,
          priority: taskPriority,
        }),
      });

      if (!response.ok) {
        console.error('Failed to save manager task');
        // Remove from local state on error
        setManagerTasks(prev => prev.filter(t => t.id !== tempId));
        alert('Failed to save task. Please try again.');
      } else {
        const data = await response.json();
        // Update with the actual task ID from backend
        if (data.task && data.task.id !== tempId) {
          setManagerTasks(prev =>
            prev.map(t => t.id === tempId ? { ...t, id: data.task.id } : t)
          );
        }
      }
    } catch (error) {
      console.error('Error saving manager task:', error);
      // Remove from local state on error
      setManagerTasks(prev => prev.filter(t => t.id !== tempId));
      alert('Error saving task. Please try again.');
    }
  };

  /* ================= TASK ROW ================= */

  const toggleExpand = (taskId: string) => {
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

  const TaskRow = ({ task }: { task: Task }) => {
    const isExpanded = expandedTaskIds.has(task.id);
    const hasDetails = task.description || task.questions?.length || task.reference || task.estimated_time_minutes || task.knowledge_capture_method;
    
    return (
      <div className={`border-b last:border-b-0 transition-all duration-200 border-[#0E1B2E]/10 ${
        darkMode
          ? "border-gray-700"
          : ""
      }`}>
        {/* MAIN ROW */}
        <div className={`px-4 py-2.5 flex justify-between items-start gap-3 transition-all duration-200 ${
          darkMode
            ? "hover:bg-gray-800/50"
            : "hover:bg-white/60"
        } ${isExpanded ? (darkMode ? "bg-gray-800/30" : "bg-white/40") : ""}`}>
          {/* LEFT */}
          <div 
            className="flex-1 cursor-pointer" 
            onClick={() => hasDetails && toggleExpand(task.id)}
          >
            <div className="flex items-start gap-2">
              {hasDetails && (
                <div className="mt-0.5">
                  {isExpanded ? (
                    <ChevronUp className={`w-4 h-4 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                  ) : (
                    <ChevronDown className={`w-4 h-4 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                  )}
                </div>
              )}
              <div className="flex-1">
                <p className={`font-medium text-sm ${
                  darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                }`}>{task.title}</p>
                <p className={`text-xs mt-0.5 ${
                  darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
                }`}>
                  Tags: <span className="font-medium">{(task.tags || ['Manual']).join(', ')}</span> • Source: <span className="font-medium">{task.source}</span>
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT */}
          <div className="flex items-center gap-2 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
        {/* PRIORITY DROPDOWN */}
        <select
          key={`${task.id}-${task.priority}-${updateCounter}`}
          value={task.priority}
          onChange={e =>
            updatePriority(
              task.id,
              task.source,
              e.target.value as Task['priority']
            )
          }
          className={`
            px-2.5 py-1
            rounded-lg
            text-xs font-medium
            border
            cursor-pointer
            focus:outline-none focus:ring-1 focus:ring-offset-0
            transition-all duration-200
            ${getPriorityStyles(task.priority, darkMode)}
          `}
        >
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        {/* ASSIGN HANDOVER */}
        <button
          onClick={() => assignHandover(task)}
          className={`
            flex items-center gap-1.5
            px-2.5 py-1.5
            rounded-lg
            text-xs font-medium
            text-white shadow-sm hover:shadow-md
            transition-all duration-200
            ${darkMode
              ? "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
              : "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
            }
          `}
        >
          <UserPlus className="w-3 h-3" />
          Assign
        </button>

        {/* NOT NEEDED */}
        {task.status !== 'not_needed' && (
          <button
            onClick={() => markTaskAsNotNeeded(task.id, task.source)}
            className={`
              flex items-center gap-1.5
              px-2.5 py-1.5
              rounded-lg
              text-xs font-medium
              text-white shadow-sm hover:shadow-md
              transition-all duration-200
              ${darkMode
                ? "bg-[#0E1B2E]/80 hover:bg-[#0E1B2E]"
                : "bg-[#0E1B2E]/80 hover:bg-[#0E1B2E]"
              }
            `}
          >
            <XCircle className="w-3 h-3" />
            Not Needed
          </button>
        )}
      </div>
    </div>
    
    {/* EXPANDED DETAILS */}
    {isExpanded && hasDetails && (
      <div className={`px-4 py-3 border-t border-[#0E1B2E]/10 ${
        darkMode ? "bg-gray-800/30" : "bg-white/20"
      }`}>
        <div className="space-y-3">
          {/* DESCRIPTION */}
          {task.description && (
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <FileText className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                  Description
                </h4>
              </div>
              <div className={`text-xs ml-5 whitespace-pre-wrap ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                {task.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
              </div>
            </div>
          )}

          {/* QUESTIONS */}
          {task.questions && task.questions.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <HelpCircle className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                  Questions ({task.questions.length})
                </h4>
              </div>
              <ul className="ml-5 space-y-1.5">
                {task.questions.map((q, idx) => (
                  <li key={idx} className={`text-xs flex items-start gap-2 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                    <span className="mt-0.5">{idx + 1}.</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* REFERENCE */}
          {task.reference && (
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <ExternalLink className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                  References
                </h4>
              </div>
              <div className={`text-xs ml-5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                {task.reference.split(', ').map((ref, idx) => (
                  <div key={idx} className="font-mono">{ref}</div>
                ))}
              </div>
            </div>
          )}

          {/* METADATA */}
          <div className={`flex flex-wrap gap-3 text-xs pt-2 border-t border-[#0E1B2E]/10 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`}>
            {task.estimated_time_minutes && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3 h-3" />
                <span>Est. {task.estimated_time_minutes} min</span>
              </div>
            )}
            {task.knowledge_capture_method && (
              <div>
                <span className="font-medium">Method:</span> {task.knowledge_capture_method.replace(/_/g, ' ')}
              </div>
            )}
          </div>
        </div>
      </div>
    )}
  </div>
  );
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading tasks..." size="md" />;
  }

  return (
    <div className="space-y-3 p-4">
      {/* ================= FILTERS ================= */}
      <div className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 px-4 py-2.5 transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/50"
          : ""
      }`}>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <label className={`text-xs font-medium ${
              darkMode ? "text-gray-300" : "text-[#0E1B2E]/70"
            }`}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value as any)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium border
                focus:outline-none focus:ring-1 focus:border-[#0E1B2E]/30
                transition-all duration-200
                ${darkMode
                  ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                  : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
                }
              `}
            >
              <option value="All">All</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="showNotNeeded"
              checked={showNotNeeded}
              onChange={e => setShowNotNeeded(e.target.checked)}
              className={`w-3.5 h-3.5 rounded focus:ring-1 cursor-pointer transition-all ${
                darkMode
                  ? "text-[#0E1B2E]/40 border border-gray-600 focus:ring-[#0E1B2E]/20"
                  : "text-[#0E1B2E] border border-[#0E1B2E]/20 focus:ring-[#0E1B2E]/10"
              }`}
            />
            <label htmlFor="showNotNeeded" className={`text-xs font-medium cursor-pointer ${
              darkMode ? "text-gray-300" : "text-[#0E1B2E]/70"
            }`}>
              Show Not Needed <span className={darkMode ? "text-[#0E1B2E]/60" : "text-[#0E1B2E]/50"}>({summary.notNeeded})</span>
            </label>
          </div>
        </div>
      </div>

      {/* 🤖 AI TASKS */}
      <div className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 overflow-hidden transition-colors duration-300 ${
        darkMode
          ? "border-gray-700/50 bg-gray-800/50"
          : ""
      }`}>
        <div className={`px-4 py-2.5 border-b border-[#0E1B2E]/10 bg-white/40 backdrop-blur-sm ${
          darkMode
            ? "border-gray-700 bg-gray-800/50"
            : ""
        }`}>
          <h3 className={`font-medium text-sm text-[#0E1B2E] ${
            darkMode
              ? "text-gray-200"
              : ""
          }`}>🤖 AI-Suggested Tasks</h3>
        </div>
        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {filteredAiTasks.length > 0 ? (
            filteredAiTasks.map(task => (
              <TaskRow key={`ai-${task.id}`} task={task} />
            ))
          ) : (
            <div className={`px-4 py-3 text-xs italic ${
              darkMode ? "text-gray-400" : "text-[#0E1B2E]/50"
            }`}>
              No tasks match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* 👤 MANAGER TASKS */}
      <div className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 overflow-hidden transition-colors duration-300 ${
        darkMode
          ? "border-gray-700/50 bg-gray-800/50"
          : ""
      }`}>
        <div className={`px-4 py-2.5 border-b border-[#0E1B2E]/10 bg-white/40 backdrop-blur-sm ${
          darkMode
            ? "border-gray-700 bg-gray-800/50"
            : ""
        }`}>
          <h3 className={`font-medium text-sm text-[#0E1B2E] ${
            darkMode
              ? "text-gray-200"
              : ""
          }`}>👤 Manager-Added Tasks</h3>
        </div>

        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {filteredManagerTasks.length > 0 ? (
            filteredManagerTasks.map(task => (
              <TaskRow key={`manager-${task.id}`} task={task} />
            ))
          ) : (
            <div className={`px-4 py-3 text-xs italic ${
              darkMode ? "text-gray-400" : "text-[#0E1B2E]/50"
            }`}>
              No tasks match the current filters.
            </div>
          )}
        </div>

        {/* ➕ ADD TASK */}
<div className={`px-4 py-3 border-t rounded-b-2xl transition-colors duration-300 ${
  darkMode
    ? "border-amber-700 bg-gradient-to-br from-amber-900/20 to-orange-900/20"
    : "border-amber-200 bg-gradient-to-br from-amber-50/50 to-orange-50/50"
}`}>
  {/* Header */}
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-center gap-2">
      <div className="w-1.5 h-6 rounded-full bg-gradient-to-b from-amber-500 to-orange-600" />
      <h4 className={`font-semibold text-xs ${
        darkMode
          ? "bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent"
          : "bg-gradient-to-r from-amber-700 to-orange-700 bg-clip-text text-transparent"
      }`}>
        Add New Task
      </h4>
    </div>
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
      darkMode
        ? "text-amber-300 bg-amber-900/50"
        : "text-amber-700 bg-amber-100"
    }`}>
      For gaps missed by AI
    </span>
  </div>

  {/* Form */}
  <div className={`
    grid grid-cols-12 gap-2 backdrop-blur-lg p-3 rounded-xl border-2 shadow-md transition-colors duration-300
    ${darkMode
      ? "bg-gray-800/80 border-amber-700"
      : "bg-white/80 border-amber-200"
    }
  `}>
    {/* TASK TITLE */}
    <input
      value={newTaskTitle}
      onChange={e => setNewTaskTitle(e.target.value)}
      placeholder="e.g. Handover retry & reconciliation logic"
      className={`
        col-span-7 px-3 py-2 rounded-lg border-2 text-xs font-medium
        placeholder-slate-400 outline-none focus:ring-2 focus:border-amber-500
        transition-all duration-200
        ${darkMode
          ? "border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:ring-amber-400"
          : "border-slate-300 bg-white text-slate-900 focus:ring-amber-500"
        }
      `}
    />

    {/* PRIORITY */}
    <select
      value={newPriority}
      onChange={e => setNewPriority(e.target.value as any)}
      className={`
        col-span-3 px-3 py-2 rounded-lg border-2 text-xs font-semibold
        outline-none focus:ring-2 focus:border-amber-500 transition-all duration-200 cursor-pointer
        ${darkMode
          ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-amber-400"
          : "border-slate-300 bg-white text-slate-900 focus:ring-amber-500"
        }
      `}
    >
      <option value="High">High</option>
      <option value="Medium">Medium</option>
      <option value="Low">Low</option>
    </select>

    {/* ADD BUTTON */}
    <button
      onClick={addManagerTask}
      className={`
        col-span-2 flex items-center justify-center gap-1 text-white
        rounded-lg text-xs font-bold shadow-md hover:shadow-lg
        transition-all duration-200
        ${darkMode
          ? "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
          : "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
        }
      `}
    >
      <span>+</span> Add
    </button>
  </div>
</div>

      </div>
    </div>
  );
}
