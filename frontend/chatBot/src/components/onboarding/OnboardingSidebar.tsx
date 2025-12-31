'use client';

import { useEffect, useState } from 'react';

interface Props {
  activeSection: 'reading' | 'qa' | 'practice' | 'bugfix';
  onChangeSection: (s: 'reading' | 'qa' | 'practice' | 'bugfix') => void;
  selectedEmployee: any;
  darkMode?: boolean;
}

export default function OnboardingSidebar({
  activeSection,
  onChangeSection,
  selectedEmployee,
  darkMode = false
}: Props) {
  const [onboardingDays, setOnboardingDays] = useState<number | null>(null);
  const [completedModules, setCompletedModules] = useState<number>(0);
  const [totalModules, setTotalModules] = useState<number>(0);
  const [completionRate, setCompletionRate] = useState<number>(0);

  // Fetch onboarding progress from API
  useEffect(() => {
    if (!selectedEmployee) {
      setOnboardingDays(null);
      setCompletedModules(0);
      setTotalModules(0);
      setCompletionRate(0);
      return;
    }

    const fetchProgress = async () => {
      try {
        const employeeId = selectedEmployee.employeeId || selectedEmployee.employee_id || selectedEmployee.id;
        if (!employeeId) return;

        const response = await fetch(`/api/onboarding/tasks?employeeId=${employeeId}`);
        if (!response.ok) {
          console.error('Failed to fetch onboarding progress');
          return;
        }
        const data = await response.json();
        
        if (data.onboarding) {
          // Calculate total modules/tasks across all sections
          const readingModules = data.onboarding.reading?.modules || [];
          const qaModules = data.onboarding.qa?.modules || [];
          const practiceTasks = data.onboarding.practice?.tasks || [];
          const bugfixTutorials = data.onboarding.bugfix?.tutorials || [];
          const bugfixChallenges = data.onboarding.bugfix?.challenges || [];
          const bugfixQuestions = data.onboarding.bugfix?.coding_questions || [];
          
          const allItems = [
            ...readingModules,
            ...qaModules,
            ...practiceTasks,
            ...bugfixTutorials,
            ...bugfixChallenges,
            ...bugfixQuestions
          ];
          
          const total = allItems.length;
          const completed = allItems.filter((item: any) => item.status === 'completed').length;
          const rate = total > 0 ? Math.round((completed / total) * 100) : 0;
          
          setTotalModules(total);
          setCompletedModules(completed);
          setCompletionRate(rate);
          
          // Calculate onboarding days from earliest completedAt date
          const completedDates = allItems
            .filter((item: any) => item.completedAt)
            .map((item: any) => new Date(item.completedAt).getTime());
          
          if (completedDates.length > 0) {
            const earliestDate = Math.min(...completedDates);
            const daysSince = Math.floor((Date.now() - earliestDate) / (1000 * 60 * 60 * 24));
            setOnboardingDays(daysSince);
          } else {
            // If no completed items, check for startedAt
            const startedDates = allItems
              .filter((item: any) => item.startedAt)
              .map((item: any) => new Date(item.startedAt).getTime());
            
            if (startedDates.length > 0) {
              const earliestDate = Math.min(...startedDates);
              const daysSince = Math.floor((Date.now() - earliestDate) / (1000 * 60 * 60 * 24));
              setOnboardingDays(daysSince);
            } else {
              setOnboardingDays(null);
            }
          }
        }
      } catch (error) {
        console.error('Error fetching onboarding progress:', error);
      }
    };

    fetchProgress();
  }, [selectedEmployee]);

  const itemClass = (key: string) =>
    `w-full text-left px-4 py-3 rounded-lg text-sm font-semibold transition ${
      activeSection === key
        ? darkMode
          ? 'bg-indigo-600 text-white shadow'
          : 'bg-indigo-600 text-white shadow'
        : darkMode
          ? 'text-gray-300 hover:bg-gray-700'
          : 'text-slate-700 hover:bg-slate-200'
    }`;

  return (
    <div className="space-y-4">

      {/* EMPLOYEE SNAPSHOT */}
      <div className={`backdrop-blur-lg rounded-2xl border-2 shadow-lg p-4 transform transition-all duration-300 hover:shadow-xl ${
        darkMode
          ? "bg-gray-800/80 border-gray-700"
          : "bg-white/80 border-slate-200/50"
      }`}>
        <div className="flex items-center gap-3 mb-3">
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center font-bold text-sm shadow-md ${
            darkMode ? "ring-2 ring-gray-700" : "ring-2 ring-white"
          }`}>
            {selectedEmployee?.name?.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase() || 'NA'}
          </div>
          <div className="flex-1 min-w-0">
            <p className={`font-bold text-sm truncate ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>{selectedEmployee?.name || 'N/A'}</p>
            <p className={`text-xs truncate ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>{selectedEmployee?.role || 'N/A'}</p>
          </div>
        </div>

        <span
          className={`inline-block px-3 py-1 rounded-full text-[10px] font-bold mb-3 shadow-sm border-2 ${
            selectedEmployee?.risk === 'high'
              ? darkMode
                ? 'bg-gradient-to-r from-red-900/50 to-red-900/70 text-red-300 border-red-700'
                : 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border-red-300'
              : selectedEmployee?.risk === 'medium'
              ? darkMode
                ? 'bg-gradient-to-r from-yellow-900/50 to-yellow-900/70 text-yellow-300 border-yellow-700'
                : 'bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border-yellow-300'
              : darkMode
                ? 'bg-gradient-to-r from-green-900/50 to-green-900/70 text-green-300 border-green-700'
                : 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border-green-300'
          }`}
        >
          {selectedEmployee?.risk?.toUpperCase() || 'MEDIUM'} RISK
        </span>

        <div className="space-y-2.5 text-xs">
          <div className={`p-2.5 rounded-lg border ${
            darkMode
              ? "bg-gradient-to-r from-gray-800 to-gray-900 border-gray-700"
              : "bg-gradient-to-r from-slate-50 to-slate-100 border-slate-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}>Onboarding Started</p>
            <p className={`font-bold text-sm ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>
              {onboardingDays ? `${onboardingDays} days ago` : 'N/A'}
            </p>
          </div>

          <div className={`p-2.5 rounded-lg border-2 ${
            darkMode
              ? "bg-gradient-to-r from-indigo-900/30 to-purple-900/30 border-indigo-700"
              : "bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-indigo-400" : "text-indigo-600"
            }`}>Progress</p>
            <p className={`font-bold text-lg ${
              darkMode ? "text-indigo-300" : "text-indigo-700"
            }`}>
              {completedModules}/{totalModules} Modules
            </p>
            <div className={`mt-2 h-2 rounded-full overflow-hidden ${
              darkMode ? "bg-gray-700" : "bg-slate-200"
            }`}>
              <div 
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
                style={{ width: `${(completedModules / totalModules) * 100}%` }}
              />
            </div>
          </div>

          <div className={`p-2.5 rounded-lg border-2 ${
            darkMode
              ? "bg-gradient-to-r from-green-900/30 to-emerald-900/30 border-green-700"
              : "bg-gradient-to-r from-green-50 to-emerald-50 border-green-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-green-400" : "text-green-600"
            }`}>Completion</p>
            <p className={`font-bold text-lg ${
              darkMode ? "text-green-300" : "text-green-700"
            }`}>
              {completionRate}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

