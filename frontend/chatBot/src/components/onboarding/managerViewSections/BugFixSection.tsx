'use client';

import { useEffect, useState } from 'react';
import Loader from '../../offboarding/Loader';

interface BugFixSectionProps {
  employeeId: string;
  darkMode?: boolean;
}

export default function BugFixSection({ employeeId, darkMode = false }: BugFixSectionProps) {
  const [tutorials, setTutorials] = useState<any[]>([]);
  const [challenges, setChallenges] = useState<any[]>([]);
  const [codingQuestions, setCodingQuestions] = useState<any[]>([]);
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
        
        if (data.onboarding?.bugfix) {
          const bugfix = data.onboarding.bugfix;
          setTutorials(bugfix.tutorials || []);
          setChallenges(bugfix.challenges || []);
          setCodingQuestions(bugfix.coding_questions || []);
          
          const allItems = [
            ...(bugfix.tutorials || []),
            ...(bugfix.challenges || []),
            ...(bugfix.coding_questions || [])
          ];
          
          const completed = allItems.filter((item: any) => item.status === 'completed').length;
          const total = allItems.length;
          const completion = total > 0 ? Math.round((completed / total) * 100) : 0;
          
          setStats({ completed, total, completion });
        }
      } catch (error) {
        console.error('Error fetching bugfix data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (employeeId) {
      fetchData();
    }
  }, [employeeId]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading bugfix progress..." size="md" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className={`text-2xl font-bold ${
          darkMode ? "text-gray-100" : "text-slate-900"
        }`}>
          Bug Fixing Progress
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
            }`}>Bugs Fixed</p>
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
            }`}>{[...tutorials, ...challenges, ...codingQuestions].filter((item: any) => item.status === 'in-progress').length}</p>
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

        {/* Tutorials */}
        {tutorials.length > 0 && (
          <div className="mb-6">
            <h4 className={`text-lg font-bold mb-3 ${
              darkMode ? "text-gray-200" : "text-slate-800"
            }`}>Tutorials</h4>
            <div className="space-y-3">
              {tutorials.map((tutorial: any, idx: number) => (
                <div
                  key={tutorial.id || idx}
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
                      {tutorial.title || tutorial.name}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      tutorial.status === 'completed'
                        ? darkMode
                          ? "bg-green-900/30 text-green-300"
                          : "bg-green-50 text-green-700"
                        : tutorial.status === 'in-progress'
                        ? darkMode
                          ? "bg-blue-900/30 text-blue-300"
                          : "bg-blue-50 text-blue-700"
                        : darkMode
                          ? "bg-gray-700 text-gray-400"
                          : "bg-gray-100 text-gray-600"
                    }`}>
                      {tutorial.status === 'completed' ? 'Completed' : 
                       tutorial.status === 'in-progress' ? 'In Progress' : 'Pending'}
                    </span>
                  </div>
                  {tutorial.progress !== undefined && (
                    <div className={`h-2 rounded-full overflow-hidden mt-2 ${
                      darkMode ? "bg-gray-700" : "bg-slate-200"
                    }`}>
                      <div
                        className={`h-full transition-all duration-300 ${
                          tutorial.status === 'completed'
                            ? "bg-gradient-to-r from-green-500 to-emerald-500"
                            : tutorial.status === 'in-progress'
                            ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                            : "bg-gray-400"
                        }`}
                        style={{ width: `${tutorial.progress || 0}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bug Fix Challenges */}
        {challenges.length > 0 && (
          <div className="mb-6">
            <h4 className={`text-lg font-bold mb-3 ${
              darkMode ? "text-gray-200" : "text-slate-800"
            }`}>Challenges</h4>
            <div className="space-y-3">
              {challenges.map((challenge: any, idx: number) => (
                <div
                  key={challenge.id || idx}
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
                      {challenge.title || challenge.name}
                    </span>
                    <div className="flex items-center gap-3">
                      {challenge.difficulty && (
                        <span className={`text-xs px-2 py-1 rounded ${
                          challenge.difficulty === 'Easy'
                            ? darkMode
                              ? "bg-green-900/30 text-green-300"
                              : "bg-green-50 text-green-700"
                            : challenge.difficulty === 'Medium'
                            ? darkMode
                              ? "bg-yellow-900/30 text-yellow-300"
                              : "bg-yellow-50 text-yellow-700"
                            : darkMode
                              ? "bg-red-900/30 text-red-300"
                              : "bg-red-50 text-red-700"
                        }`}>
                          {challenge.difficulty}
                        </span>
                      )}
                      <span className={`text-xs px-2 py-1 rounded ${
                        challenge.status === 'completed'
                          ? darkMode
                            ? "bg-green-900/30 text-green-300"
                            : "bg-green-50 text-green-700"
                          : challenge.status === 'in-progress'
                          ? darkMode
                            ? "bg-blue-900/30 text-blue-300"
                            : "bg-blue-50 text-blue-700"
                          : darkMode
                            ? "bg-gray-700 text-gray-400"
                            : "bg-gray-100 text-gray-600"
                      }`}>
                        {challenge.status === 'completed' ? 'Completed' : 
                         challenge.status === 'in-progress' ? 'In Progress' : 'Pending'}
                      </span>
                    </div>
                  </div>
                  {challenge.progress !== undefined && (
                    <div className={`h-2 rounded-full overflow-hidden mt-2 ${
                      darkMode ? "bg-gray-700" : "bg-slate-200"
                    }`}>
                      <div
                        className={`h-full transition-all duration-300 ${
                          challenge.status === 'completed'
                            ? "bg-gradient-to-r from-green-500 to-emerald-500"
                            : challenge.status === 'in-progress'
                            ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                            : "bg-gray-400"
                        }`}
                        style={{ width: `${challenge.progress || 0}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Coding Questions */}
        {codingQuestions.length > 0 && (
          <div>
            <h4 className={`text-lg font-bold mb-3 ${
              darkMode ? "text-gray-200" : "text-slate-800"
            }`}>Coding Questions</h4>
            <div className="space-y-3">
              {codingQuestions.map((question: any, idx: number) => (
                <div
                  key={question.id || idx}
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
                      {question.title || question.name}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      question.status === 'completed'
                        ? darkMode
                          ? "bg-green-900/30 text-green-300"
                          : "bg-green-50 text-green-700"
                        : question.status === 'in-progress'
                        ? darkMode
                          ? "bg-blue-900/30 text-blue-300"
                          : "bg-blue-50 text-blue-700"
                        : darkMode
                          ? "bg-gray-700 text-gray-400"
                          : "bg-gray-100 text-gray-600"
                    }`}>
                      {question.status === 'completed' ? 'Completed' : 
                       question.status === 'in-progress' ? 'In Progress' : 'Pending'}
                    </span>
                  </div>
                  {question.progress !== undefined && (
                    <div className={`h-2 rounded-full overflow-hidden mt-2 ${
                      darkMode ? "bg-gray-700" : "bg-slate-200"
                    }`}>
                      <div
                        className={`h-full transition-all duration-300 ${
                          question.status === 'completed'
                            ? "bg-gradient-to-r from-green-500 to-emerald-500"
                            : question.status === 'in-progress'
                            ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                            : "bg-gray-400"
                        }`}
                        style={{ width: `${question.progress || 0}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {tutorials.length === 0 && challenges.length === 0 && codingQuestions.length === 0 && (
          <div className={`text-center py-8 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
            <p>No bugfix tasks found</p>
          </div>
        )}
      </div>
    </div>
  );
}

