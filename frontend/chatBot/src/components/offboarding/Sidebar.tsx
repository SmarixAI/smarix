'use client';

import { useEffect, useState } from 'react';

interface Props {
  activeSection: 'finalcall' | 'handover' | 'documentation';
  onChangeSection: (s: 'finalcall' | 'handover' | 'documentation') => void;
  selectedEmployee: any;
  darkMode?: boolean;
}

export default function Sidebar({
  activeSection,
  onChangeSection,
  selectedEmployee,
  darkMode = false
}: Props) {
  const [effectiveWorkdays, setEffectiveWorkdays] = useState<number | null>(null);
  const [highRiskTasksPending, setHighRiskTasksPending] = useState<number>(0);

  // Calculate effective workdays remaining
  useEffect(() => {
    if (!selectedEmployee?.lastDay) {
      setEffectiveWorkdays(null);
      return;
    }

    try {
      const lastDay = new Date(selectedEmployee.lastDay);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      lastDay.setHours(0, 0, 0, 0);

      // Calculate total days between today and last day
      const diffTime = lastDay.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays <= 0) {
        setEffectiveWorkdays(0);
        return;
      }

      // Subtract 40% for non-working days (weekends + vacations)
      const effectiveDays = Math.round(diffDays * 0.6);
      setEffectiveWorkdays(effectiveDays);
    } catch (error) {
      console.error('Error calculating workdays:', error);
      setEffectiveWorkdays(null);
    }
  }, [selectedEmployee?.lastDay]);

  // Fetch and count high-risk tasks
  useEffect(() => {
    if (!selectedEmployee?.employeeId) {
      setHighRiskTasksPending(0);
      return;
    }

    const fetchTasks = async () => {
      try {
        const response = await fetch('/api/offboarding/tasks');
        if (!response.ok) {
          console.error('Failed to fetch tasks data');
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) return;

        const employee = data.employees.find(
          (e: any) => e.employeeId === selectedEmployee.employeeId
        );

        if (!employee) return;

        // Combine AI and manager tasks
        const aiTasks = employee.tasks?.ai ?? [];
        const managerTasks = employee.tasks?.manager ?? [];
        const allTasks = [...aiTasks, ...managerTasks];

        // Count high priority tasks that are not marked as "not_needed"
        const highRiskCount = allTasks.filter(
          (task: any) => 
            task.priority === 'High' && 
            task.status !== 'not_needed'
        ).length;

        setHighRiskTasksPending(highRiskCount);
      } catch (error) {
        console.error('Error fetching tasks:', error);
      }
    };

    fetchTasks();
  }, [selectedEmployee?.employeeId]);

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
            {selectedEmployee.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div className="flex-1 min-w-0">
            <p className={`font-bold text-sm truncate ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>{selectedEmployee.name}</p>
            <p className={`text-xs truncate ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>{selectedEmployee.designation || selectedEmployee.role}</p>
          </div>
        </div>

        <span
          className={`inline-block px-3 py-1 rounded-full text-[10px] font-bold mb-3 shadow-sm border-2 ${
            selectedEmployee.risk === 'high'
              ? darkMode
                ? 'bg-gradient-to-r from-red-900/50 to-red-900/70 text-red-300 border-red-700'
                : 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border-red-300'
              : selectedEmployee.risk === 'medium'
              ? darkMode
                ? 'bg-gradient-to-r from-yellow-900/50 to-yellow-900/70 text-yellow-300 border-yellow-700'
                : 'bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border-yellow-300'
              : darkMode
                ? 'bg-gradient-to-r from-green-900/50 to-green-900/70 text-green-300 border-green-700'
                : 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border-green-300'
          }`}
        >
          {selectedEmployee.risk.toUpperCase()} RISK
        </span>

        <div className="space-y-2.5 text-xs">
          <div className={`p-2.5 rounded-lg border ${
            darkMode
              ? "bg-gradient-to-r from-gray-800 to-gray-900 border-gray-700"
              : "bg-gradient-to-r from-slate-50 to-slate-100 border-slate-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}>Last Working Day</p>
            <p className={`font-bold text-sm ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>
              {selectedEmployee.lastDay || 'Not set'}
            </p>
          </div>

          <div className={`p-2.5 rounded-lg border-2 ${
            darkMode
              ? "bg-gradient-to-r from-indigo-900/30 to-purple-900/30 border-indigo-700"
              : "bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-indigo-400" : "text-indigo-600"
            }`}>Effective Workdays</p>
            <p className={`font-bold text-lg ${
              darkMode ? "text-indigo-300" : "text-indigo-700"
            }`}>
              {effectiveWorkdays !== null 
                ? `${effectiveWorkdays} ${effectiveWorkdays === 1 ? 'Day' : 'Days'}`
                : 'N/A'}
            </p>
          </div>

          <div className={`p-2.5 rounded-lg border-2 ${
            darkMode
              ? "bg-gradient-to-r from-red-900/30 to-pink-900/30 border-red-700"
              : "bg-gradient-to-r from-red-50 to-pink-50 border-red-200"
          }`}>
            <p className={`text-[10px] mb-0.5 font-semibold ${
              darkMode ? "text-red-400" : "text-red-600"
            }`}>High-Risk Tasks</p>
            <p className={`font-bold text-lg ${
              darkMode ? "text-red-300" : "text-red-700"
            }`}>
              {highRiskTasksPending} {highRiskTasksPending === 1 ? 'Task' : 'Tasks'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
