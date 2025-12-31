'use client';

import { useEffect, useState } from 'react';
import Loader from '../../offboarding/Loader';

interface QASectionProps {
  employeeId: string;
  darkMode?: boolean;
}

export default function QASection({ employeeId, darkMode = false }: QASectionProps) {
  const [modules, setModules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ answered: 0, total: 0, avgScore: 0, completion: 0 });

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
        
        if (data.onboarding?.qa?.modules) {
          const qaModules = data.onboarding.qa.modules;
          setModules(qaModules);
          
          const completed = qaModules.filter((m: any) => m.status === 'completed').length;
          const total = qaModules.length;
          const completion = total > 0 ? Math.round((completed / total) * 100) : 0;
          
          const scores = qaModules
            .filter((m: any) => m.score !== null && m.score !== undefined)
            .map((m: any) => {
              const score = m.score || 0;
              const totalQ = m.totalQuestions || 5;
              return (score / totalQ) * 100;
            });
          
          const avgScore = scores.length > 0 
            ? Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
            : 0;
          
          setStats({ answered: completed, total, avgScore, completion });
        }
      } catch (error) {
        console.error('Error fetching Q&A data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (employeeId) {
      fetchData();
    }
  }, [employeeId]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading Q&A progress..." size="md" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className={`text-2xl font-bold ${
          darkMode ? "text-gray-100" : "text-slate-900"
        }`}>
          Q&A Session Progress
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
            }`}>Questions Answered</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-indigo-300" : "text-indigo-700"
            }`}>{stats.answered}/{stats.total}</p>
          </div>
          <div className={`p-4 rounded-xl ${
            darkMode ? "bg-blue-900/30" : "bg-blue-50"
          }`}>
            <p className={`text-xs font-semibold mb-1 ${
              darkMode ? "text-blue-400" : "text-blue-600"
            }`}>Average Score</p>
            <p className={`text-2xl font-bold ${
              darkMode ? "text-blue-300" : "text-blue-700"
            }`}>{stats.avgScore}%</p>
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

        {/* Q&A Modules */}
        <div className="space-y-3">
          {modules.length === 0 ? (
            <div className={`text-center py-8 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
              <p>No Q&A modules found</p>
            </div>
          ) : (
            modules.map((module: any, idx: number) => {
              const scorePercent = module.totalQuestions && module.score !== null
                ? Math.round((module.score / module.totalQuestions) * 100)
                : null;
              
              return (
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
                <div className="flex items-center gap-3">
                  {scorePercent !== null && (
                    <span className={`text-sm font-bold ${
                      darkMode ? "text-indigo-300" : "text-indigo-700"
                    }`}>
                      Score: {scorePercent}% ({module.score}/{module.totalQuestions})
                    </span>
                  )}
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
              </div>
            </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

