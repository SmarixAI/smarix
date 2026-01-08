'use client';

import { useEffect, useState } from 'react';

interface Props {
  activeSection: 'finalcall' | 'handover' | 'documentation';
  onChangeSection: (s: 'finalcall' | 'handover' | 'documentation') => void;
  selectedEmployee: any;
  darkMode?: boolean; // Kept for backwards compatibility but not used
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

  return (
    <div className="space-y-4">
      {/* EMPLOYEE SNAPSHOT */}
      <div className="rounded-lg border border-gray-200 shadow-sm p-4 bg-white">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-gray-800 text-white flex items-center justify-center font-semibold text-sm">
            {selectedEmployee.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate text-gray-900">{selectedEmployee.name}</p>
            <p className="text-xs truncate text-gray-600">{selectedEmployee.designation || selectedEmployee.role}</p>
          </div>
        </div>

        <span
          className={`inline-block px-3 py-1 rounded-full text-[10px] font-semibold mb-3 shadow-sm border ${
            selectedEmployee.risk === 'high'
              ? 'bg-red-50 text-red-700 border-red-200'
              : selectedEmployee.risk === 'medium'
              ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
              : 'bg-green-50 text-green-700 border-green-200'
          }`}
        >
          {selectedEmployee.risk.toUpperCase()} RISK
        </span>

        <div className="space-y-2.5 text-xs">
          <div className="p-2.5 rounded-lg border bg-gray-50 border-gray-200">
            <p className="text-[10px] mb-0.5 font-semibold text-gray-600">Last Working Day</p>
            <p className="font-semibold text-sm text-gray-900">
              {selectedEmployee.lastDay || 'Not set'}
            </p>
          </div>

          <div className="p-2.5 rounded-lg border-2 bg-gray-50 border-gray-200">
            <p className="text-[10px] mb-0.5 font-semibold text-gray-600">Effective Workdays</p>
            <p className="font-semibold text-lg text-gray-900">
              {effectiveWorkdays !== null 
                ? `${effectiveWorkdays} ${effectiveWorkdays === 1 ? 'Day' : 'Days'}`
                : 'N/A'}
            </p>
          </div>

          <div className="p-2.5 rounded-lg border-2 bg-gray-50 border-gray-200">
            <p className="text-[10px] mb-0.5 font-semibold text-gray-600">High-Risk Tasks</p>
            <p className="font-semibold text-lg text-gray-900">
              {highRiskTasksPending} {highRiskTasksPending === 1 ? 'Task' : 'Tasks'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
