'use client';

import { useEffect, useState } from 'react';
import { CheckCircle } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type Task = {
  id: string;
  title: string;
  priority: 'High' | 'Medium' | 'Low';
  tags: string[];
  source: 'AI' | 'Manager';
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

export default function EmployeeFinalCallSection({ employeeId, darkMode = false }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [acknowledged, setAcknowledged] = useState(false);
  const [loading, setLoading] = useState(true);

  // ✅ NEW: per-task completion state
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(
    new Set()
  );

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
          console.log('No employees found in tasks data');
          setLoading(false);
          return;
        }

        console.log('Looking for employeeId:', employeeId);
        console.log('Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        const employee =
          data.employees.find((e: any) => 
            e.employeeId === employeeId || 
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
          ) ?? data.employees[0];
        
        console.log('Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Employee tasks:', employee?.tasks);

        // Combine tasks and ensure they have tags
        const aiTasks = (employee.tasks?.ai ?? []).map((task: any) => ({
          ...task,
          tags: task.tags || ['Manual']
        }));
        
        const managerTasks = (employee.tasks?.manager ?? []).map((task: any) => ({
          ...task,
          tags: task.tags || ['Manual']
        }));

        const combinedTasks = [...aiTasks, ...managerTasks];

        setTasks(combinedTasks);
        setCompletedTaskIds(new Set()); // reset on employee change
      } catch (error) {
        console.error('Error fetching tasks data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY ================= */

  const summary = {
    total: tasks.length,
    explained: completedTaskIds.size,
    remaining: tasks.length - completedTaskIds.size,
    high: tasks.filter(t => t.priority === 'High').length
  };

  /* ================= ACTION ================= */

  const markTaskExplained = (taskId: string) => {
    setCompletedTaskIds(prev => new Set(prev).add(taskId));
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading tasks..." size="md" />;
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
            Your Final Call Tasks
          </h3>
          <p className={`text-xs mt-1 ${
            darkMode ? "text-gray-400" : "text-slate-600"
          }`}>
            Topics you must explain before your last working day
          </p>
        </div>

        <div className="grid grid-cols-4 gap-4 px-5 py-4">
          <SummaryCard label="Total Tasks" value={summary.total} darkMode={darkMode} />
          <SummaryCard label="Explained" value={summary.explained} tone="green" darkMode={darkMode} />
          <SummaryCard label="Remaining" value={summary.remaining} tone="yellow" darkMode={darkMode} />
          <SummaryCard label="High Priority" value={summary.high} tone="red" darkMode={darkMode} />
        </div>
      </div>

      {/* ================= TASK LIST ================= */}
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
            Knowledge Transfer Topics
          </h3>
        </div>

        <div className={darkMode ? "divide-y divide-gray-700" : "divide-y"}>
          {tasks.map(task => {
            const isDone = completedTaskIds.has(task.id);

            return (
              <div
                key={task.id}
                className={`
                  px-5 py-4 flex justify-between items-start gap-4
                  ${isDone ? 'opacity-60' : ''}
                `}
              >
                {/* LEFT */}
                <div className="flex-1">
                  <p className={`font-semibold ${
                    darkMode ? "text-gray-100" : "text-slate-900"
                  }`}>
                    {task.title}
                  </p>
                  <p className={`text-xs mt-1 ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`}>
                    Source: {task.source} • Tags: {(task.tags || ['Manual']).join(', ')}
                  </p>
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

                  {/* ACTION */}
                  {isDone ? (
                    <span className={`flex items-center gap-1.5 text-xs font-semibold ${
                      darkMode ? "text-green-400" : "text-green-700"
                    }`}>
                      <CheckCircle className="w-4 h-4" />
                      Explained
                    </span>
                  ) : (
                    <button
                      onClick={() => markTaskExplained(task.id)}
                      className={`
                        px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition
                        ${darkMode
                          ? "bg-indigo-600 hover:bg-indigo-700"
                          : "bg-indigo-600 hover:bg-indigo-700"
                        }
                      `}
                    >
                      Mark as Explained
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ================= FINAL ACK ================= */}
      <div className={`rounded-2xl border p-5 flex items-center justify-between transition-colors duration-300 ${
        darkMode
          ? "border-indigo-700 bg-indigo-900/30"
          : "border-indigo-200 bg-indigo-50"
      }`}>
        <div>
          <p className={`font-semibold ${
            darkMode ? "text-indigo-200" : "text-indigo-900"
          }`}>
            Final Acknowledgement
          </p>
          <p className={`text-xs mt-1 ${
            darkMode ? "text-indigo-300" : "text-indigo-700"
          }`}>
            Confirm that you have explained all critical knowledge areas
          </p>
        </div>

        <button
          disabled={acknowledged || summary.remaining > 0}
          onClick={() => setAcknowledged(true)}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-xl
            text-sm font-semibold transition
            ${
              acknowledged
                ? 'bg-green-600 text-white'
                : summary.remaining > 0
                ? 'bg-slate-300 text-slate-600 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }
          `}
        >
          <CheckCircle className="w-4 h-4" />
          {acknowledged ? 'Acknowledged' : 'Acknowledge Completion'}
        </button>
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
  tone?: 'red' | 'yellow' | 'green' | 'slate';
  darkMode?: boolean;
}) {
  const getTones = (tone: string, darkMode: boolean): string => {
    if (darkMode) {
      return tone === 'red'
        ? 'bg-red-900/30 text-red-300'
        : tone === 'yellow'
        ? 'bg-yellow-900/30 text-yellow-300'
        : tone === 'green'
        ? 'bg-green-900/30 text-green-300'
        : 'bg-gray-800 text-gray-100';
    }
    return tone === 'red'
      ? 'bg-red-50 text-red-700'
      : tone === 'yellow'
      ? 'bg-yellow-50 text-yellow-800'
      : tone === 'green'
      ? 'bg-green-50 text-green-800'
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
