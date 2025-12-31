'use client';

import { useEffect, useState } from 'react';
import Loader from '../../offboarding/Loader';

interface ReadingSectionProps {
  employeeId: string;
  darkMode?: boolean;
}

export default function ReadingSection({ employeeId, darkMode = false }: ReadingSectionProps) {
  const [modules, setModules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ completed: 0, total: 0, completionRate: 0 });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log('ReadingSection - Fetching data for employeeId:', employeeId);
        const response = await fetch(`/api/onboarding/tasks?employeeId=${employeeId}`);
        
        if (!response.ok) {
          const errorData = await response.json();
          console.error('Failed to fetch onboarding tasks:', response.status, errorData);
          setLoading(false);
          return;
        }
        
        const data = await response.json();
        console.log('ReadingSection - Received data:', data);
        console.log('ReadingSection - Onboarding data:', data.onboarding);
        console.log('ReadingSection - Reading modules:', data.onboarding?.reading?.modules);
        
        if (data.onboarding?.reading?.modules) {
          const readingModules = data.onboarding.reading.modules;
          setModules(readingModules);
          
          const completed = readingModules.filter((m: any) => m.status === 'completed').length;
          const total = readingModules.length;
          const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
          
          setStats({ completed, total, completionRate });
          console.log('ReadingSection - Set modules:', readingModules.length, 'Stats:', { completed, total, completionRate });
        } else {
          console.warn('ReadingSection - No reading modules found in data');
          setModules([]);
          setStats({ completed: 0, total: 0, completionRate: 0 });
        }
      } catch (error) {
        console.error('Error fetching reading data:', error);
        setModules([]);
        setStats({ completed: 0, total: 0, completionRate: 0 });
      } finally {
        setLoading(false);
      }
    };

    if (employeeId) {
      fetchData();
    } else {
      console.warn('ReadingSection - No employeeId provided');
      setLoading(false);
    }
  }, [employeeId]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading reading progress..." size="md" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className={`text-2xl font-bold ${
          darkMode ? "text-gray-100" : "text-slate-900"
        }`}>
          Reading & Overview Progress
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
            }`}>Modules Completed</p>
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
            }`}>{modules.filter((m: any) => m.status === 'in-progress').length}</p>
          </div>
          <div className={`p-4 rounded-xl ${
            darkMode ? "bg-green-900/30" : "bg-green-50"
          }`}>
            <p className={`text-xs font-semibold mb-1 ${
              darkMode ? "text-green-400" : "text-green-600"
            }`}>Completion Rate</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-green-300" : "text-green-700"
            }`}>{stats.completionRate}%</p>
          </div>
        </div>

        {/* Module List */}
        <div className="space-y-3">
          {modules.length === 0 ? (
            <div className={`text-center py-8 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
              <p>No reading modules found</p>
            </div>
          ) : (
            modules.map((module: any, idx: number) => (
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
                  {module.title || module.name}
                </span>
                <span className={`text-xs px-2 py-1 rounded ${
                  module.status === 'completed'
                    ? darkMode
                      ? "bg-green-900/30 text-green-300"
                      : "bg-green-50 text-green-700"
                    : module.status === 'in-progress'
                    ? darkMode
                      ? "bg-blue-900/30 text-blue-300"
                      : "bg-blue-50 text-blue-700"
                    : darkMode
                      ? "bg-gray-700 text-gray-400"
                      : "bg-gray-100 text-gray-600"
                }`}>
                  {module.status === 'completed' ? 'Completed' : 
                   module.status === 'in-progress' ? 'In Progress' : 'Pending'}
                </span>
              </div>
              <div className={`h-2 rounded-full overflow-hidden ${
                darkMode ? "bg-gray-700" : "bg-slate-200"
              }`}>
                <div
                  className={`h-full transition-all duration-300 ${
                    module.status === 'completed'
                      ? "bg-gradient-to-r from-green-500 to-emerald-500"
                      : module.status === 'in-progress'
                      ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                      : "bg-gray-400"
                  }`}
                  style={{ width: `${module.progress || 0}%` }}
                />
              </div>
            </div>
          )))}
        </div>
      </div>
    </div>
  );
}

