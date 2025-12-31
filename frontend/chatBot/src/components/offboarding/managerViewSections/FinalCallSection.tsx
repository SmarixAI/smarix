'use client';

import { useEffect, useState } from 'react';
import { UserPlus, XCircle } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type Task = {
  id: string;
  title: string;
  priority: 'High' | 'Medium' | 'Low';
  tags: string[];
  source: 'AI' | 'Manager';
  status?: 'active' | 'inactive' | 'not_needed';
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

  const TaskRow = ({ task }: { task: Task }) => (
    <div className={`px-4 py-3 flex justify-between items-start gap-3 border-b last:border-b-0 transition-all duration-200 ${
      darkMode
        ? "border-gray-700 hover:bg-gray-800/50"
        : "border-slate-200 hover:bg-white/50"
    }`}>
      {/* LEFT */}
      <div className="flex-1">
        <p className={`font-semibold text-sm ${
          darkMode ? "text-gray-100" : "text-slate-900"
        }`}>{task.title}</p>
        <p className={`text-xs mt-1 ${
          darkMode ? "text-gray-400" : "text-slate-600"
        }`}>
          Tags: <span className="font-medium">{(task.tags || ['Manual']).join(', ')}</span> • Source: <span className="font-medium">{task.source}</span>
        </p>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-2 flex-shrink-0">
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
            px-2.5 py-1.5
            rounded-lg
            text-xs font-semibold
            border-2
            cursor-pointer
            focus:outline-none focus:ring-2 focus:ring-offset-1
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
          className="
            flex items-center gap-1.5
            px-3 py-1.5
            rounded-lg
            text-xs font-semibold
            bg-gradient-to-r from-indigo-500 to-purple-600 text-white
            hover:from-indigo-600 hover:to-purple-700
            shadow-sm hover:shadow-md
            transition-all duration-200
          "
        >
          <UserPlus className="w-3.5 h-3.5" />
          Assign
        </button>

        {/* NOT NEEDED */}
        {task.status !== 'not_needed' && (
          <button
            onClick={() => markTaskAsNotNeeded(task.id, task.source)}
            className="
              flex items-center gap-1.5
              px-3 py-1.5
              rounded-lg
              text-xs font-semibold
              bg-gradient-to-r from-red-500 to-pink-600 text-white
              hover:from-red-600 hover:to-pink-700
              shadow-sm hover:shadow-md
              transition-all duration-200
            "
          >
            <XCircle className="w-3.5 h-3.5" />
            Not Needed
          </button>
        )}
      </div>
    </div>
  );

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading tasks..." size="md" />;
  }

  return (
    <div className="space-y-4">

      {/* ================= OVERALL SUMMARY ================= */}
<div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg overflow-hidden transition-colors duration-300 ${
  darkMode
    ? "border-gray-700 bg-gray-800/80"
    : "border-slate-200/50 bg-white/80"
}`}>
  <div className={`px-4 py-2.5 border-b ${
    darkMode
      ? "border-gray-700 bg-gradient-to-r from-indigo-900/50 to-purple-900/50"
      : "border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50"
  }`}>
    <h3 className={`font-bold text-sm ${
      darkMode
        ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
        : "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent"
    }`}>
      Overall Task Summary
    </h3>
  </div>

  <div className="grid grid-cols-6 gap-2 px-4 py-3">
    {/* TOTAL */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-gray-700 bg-gradient-to-br from-gray-800 to-gray-900"
        : "border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-gray-400" : "text-slate-600"
      }`}>Total</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-gray-100" : "text-slate-900"
      }`}>
        {summary.total}
      </p>
    </div>

    {/* HIGH */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-red-700 bg-gradient-to-br from-red-900/30 to-red-900/50"
        : "border-red-200 bg-gradient-to-br from-red-50 to-red-100"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-red-400" : "text-red-600"
      }`}>High</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-red-300" : "text-red-700"
      }`}>
        {summary.high}
      </p>
    </div>

    {/* MEDIUM */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-yellow-700 bg-gradient-to-br from-yellow-900/30 to-yellow-900/50"
        : "border-yellow-200 bg-gradient-to-br from-yellow-50 to-yellow-100"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-yellow-400" : "text-yellow-700"
      }`}>Medium</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-yellow-300" : "text-yellow-800"
      }`}>
        {summary.medium}
      </p>
    </div>

    {/* LOW */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-green-700 bg-gradient-to-br from-green-900/30 to-green-900/50"
        : "border-green-200 bg-gradient-to-br from-green-50 to-green-100"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-green-400" : "text-green-700"
      }`}>Low</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-green-300" : "text-green-800"
      }`}>
        {summary.low}
      </p>
    </div>

    {/* REMAINING */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-indigo-700 bg-gradient-to-br from-indigo-900/30 to-purple-900/30"
        : "border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-indigo-400" : "text-indigo-700"
      }`}>Remaining</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-indigo-300" : "text-indigo-800"
      }`}>
        {summary.remaining}
      </p>
    </div>

    {/* YET TO ASSIGN */}
    <div className={`rounded-xl border-2 px-3 py-2 shadow-sm hover:shadow-md transition-all duration-200 ${
      darkMode
        ? "border-gray-600 bg-gradient-to-br from-gray-700 to-gray-800"
        : "border-slate-300 bg-gradient-to-br from-slate-100 to-slate-200"
    }`}>
      <p className={`text-[10px] font-bold mb-0.5 ${
        darkMode ? "text-gray-400" : "text-slate-700"
      }`}>To Assign</p>
      <p className={`text-xl font-extrabold ${
        darkMode ? "text-gray-100" : "text-slate-900"
      }`}>
        {summary.yetToAssign}
      </p>
    </div>
    </div>
</div>

      {/* ================= FILTERS ================= */}
      <div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg p-3 transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/80"
          : "border-slate-200/50 bg-white/80"
      }`}>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className={`text-xs font-semibold ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value as any)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-semibold border-2
                focus:outline-none focus:ring-2 focus:border-indigo-500
                transition-all duration-200
                ${darkMode
                  ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                  : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
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
              className={`w-4 h-4 rounded focus:ring-2 cursor-pointer transition-all ${
                darkMode
                  ? "text-indigo-400 border-2 border-gray-600 focus:ring-indigo-400"
                  : "text-indigo-600 border-2 border-slate-300 focus:ring-indigo-500"
              }`}
            />
            <label htmlFor="showNotNeeded" className={`text-xs font-semibold cursor-pointer ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>
              Show Not Needed <span className={darkMode ? "text-indigo-400" : "text-indigo-600"}>({summary.notNeeded})</span>
            </label>
          </div>
        </div>
      </div>

      {/* 🤖 AI TASKS */}
      <div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg overflow-hidden transition-colors duration-300 ${
        darkMode
          ? "border-indigo-700/50 bg-gradient-to-br from-indigo-900/30 to-purple-900/30"
          : "border-indigo-200/50 bg-gradient-to-br from-indigo-50/80 to-purple-50/80"
      }`}>
        <div className={`px-4 py-2.5 border-b ${
          darkMode
            ? "border-indigo-700 bg-gradient-to-r from-indigo-900/50 to-purple-900/50"
            : "border-indigo-200 bg-gradient-to-r from-indigo-100 to-purple-100"
        }`}>
          <h3 className={`font-bold text-sm ${
            darkMode
              ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
              : "bg-gradient-to-r from-indigo-700 to-purple-700 bg-clip-text text-transparent"
          }`}>🤖 AI-Suggested Tasks</h3>
        </div>
        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {filteredAiTasks.length > 0 ? (
            filteredAiTasks.map(task => (
              <TaskRow key={`ai-${task.id}`} task={task} />
            ))
          ) : (
            <div className={`px-5 py-4 text-sm italic ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}>
              No tasks match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* 👤 MANAGER TASKS */}
      <div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg overflow-hidden transition-colors duration-300 ${
        darkMode
          ? "border-amber-700/50 bg-gradient-to-br from-amber-900/30 to-orange-900/30"
          : "border-amber-200/50 bg-gradient-to-br from-amber-50/80 to-orange-50/80"
      }`}>
        <div className={`px-4 py-2.5 border-b ${
          darkMode
            ? "border-amber-700 bg-gradient-to-r from-amber-900/50 to-orange-900/50"
            : "border-amber-200 bg-gradient-to-r from-amber-100 to-orange-100"
        }`}>
          <h3 className={`font-bold text-sm ${
            darkMode
              ? "bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent"
              : "bg-gradient-to-r from-amber-700 to-orange-700 bg-clip-text text-transparent"
          }`}>👤 Manager-Added Tasks</h3>
        </div>

        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {filteredManagerTasks.length > 0 ? (
            filteredManagerTasks.map(task => (
              <TaskRow key={`manager-${task.id}`} task={task} />
            ))
          ) : (
            <div className={`px-5 py-4 text-sm italic ${
              darkMode ? "text-gray-400" : "text-slate-500"
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
