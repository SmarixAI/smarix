'use client';

import { useEffect, useState } from 'react';
import Loader from '../../offboarding/Loader';

interface PracticeSectionProps {
  employeeId: string;
  darkMode?: boolean;
}

export default function PracticeSection({ employeeId, darkMode = false }: PracticeSectionProps) {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ completed: 0, total: 0, completion: 0 });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/onboarding/tasks?employeeId=${employeeId}`);
        if (!response.ok) {
          console.error('Failed to fetch onboarding tasks');
          setLoading(false);
          return;
        }
        const data = await response.json();
        
        if (data.onboarding?.practice?.tasks) {
          const practiceTasks = data.onboarding.practice.tasks;
          setTasks(practiceTasks);
          
          const completed = practiceTasks.filter((t: any) => t.status === 'completed').length;
          const total = practiceTasks.length;
          const completion = total > 0 ? Math.round((completed / total) * 100) : 0;
          
          setStats({ completed, total, completion });
        }
      } catch (error) {
        console.error('Error fetching practice data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (employeeId) {
      fetchData();
    }
  }, [employeeId]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading practice progress..." size="md" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className={`text-2xl font-bold ${
          darkMode ? "text-gray-100" : "text-slate-900"
        }`}>
          Practice Tasks Progress
        </h3>
      </div>

      {/* Progress Overview */}
      <div className={`rounded-2xl p-6 border ${
        darkMode
          ? "bg-gray-900/50 border-gray-700"
          : "bg-slate-50 border-slate-200"
      }`}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className={`p-4 rounded-xl ${
            darkMode ? "bg-indigo-900/30" : "bg-indigo-50"
          }`}>
            <p className={`text-xs font-semibold mb-1 ${
              darkMode ? "text-indigo-400" : "text-indigo-600"
            }`}>Tasks Completed</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-indigo-300" : "text-indigo-700"
            }`}>{stats.completed}/{stats.total}</p>
          </div>
          <div className={`p-4 rounded-xl ${
            darkMode ? "bg-blue-900/30" : "bg-blue-50"
          }`}>
            <p className={`text-xs font-semibold mb-1 ${
              darkMode ? "text-blue-400" : "text-blue-600"
            }`}>In Progress</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-blue-300" : "text-blue-700"
            }`}>{tasks.filter((t: any) => t.status === 'in-progress').length}</p>
          </div>
          <div className={`p-4 rounded-xl ${
            darkMode ? "bg-green-900/30" : "bg-green-50"
          }`}>
            <p className={`text-xs font-semibold mb-1 ${
              darkMode ? "text-green-400" : "text-green-600"
            }`}>Completion</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-green-300" : "text-green-700"
            }`}>{stats.completion}%</p>
          </div>
        </div>

        {/* Practice Tasks */}
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <div className={`text-center py-8 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
              <p>No practice tasks found</p>
            </div>
          ) : (
            tasks.map((task: any, idx: number) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${
                darkMode
                  ? "bg-gray-800 border-gray-700"
                  : "bg-white border-slate-200"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`font-semibold ${
                  darkMode ? "text-gray-100" : "text-slate-900"
                }`}>
                  {task.title || task.name}
                </span>
                <div className="flex items-center gap-3">
                  {task.difficulty && (
                    <span className={`text-xs px-2 py-1 rounded ${
                      task.difficulty === 'Easy'
                        ? darkMode ? "bg-green-900/30 text-green-300" : "bg-green-50 text-green-700"
                        : task.difficulty === 'Medium'
                        ? darkMode ? "bg-yellow-900/30 text-yellow-300" : "bg-yellow-50 text-yellow-700"
                        : darkMode ? "bg-red-900/30 text-red-300" : "bg-red-50 text-red-700"
                    }`}>
                      {task.difficulty}
                    </span>
                  )}
                  <span className={`text-xs px-2 py-1 rounded ${
                    task.status === 'completed'
                      ? darkMode
                        ? "bg-green-900/30 text-green-300"
                        : "bg-green-50 text-green-700"
                      : task.status === 'in-progress'
                      ? darkMode
                        ? "bg-blue-900/30 text-blue-300"
                        : "bg-blue-50 text-blue-700"
                      : darkMode
                        ? "bg-gray-700 text-gray-400"
                        : "bg-gray-100 text-gray-600"
                  }`}>
                    {task.status === 'completed' ? 'Completed' : 
                     task.status === 'in-progress' ? 'In Progress' : 'Pending'}
                  </span>
                </div>
              </div>
              {task.progress !== undefined && (
                <div className={`h-2 rounded-full overflow-hidden mt-2 ${
                  darkMode ? "bg-gray-700" : "bg-slate-200"
                }`}>
                  <div
                    className={`h-full transition-all duration-300 ${
                      task.status === 'completed'
                        ? "bg-gradient-to-r from-green-500 to-emerald-500"
                        : task.status === 'in-progress'
                        ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                        : "bg-gray-400"
                    }`}
                    style={{ width: `${task.progress || 0}%` }}
                  />
                </div>
              )}
            </div>
          )))}
        </div>
      </div>
    </div>
  );
}

