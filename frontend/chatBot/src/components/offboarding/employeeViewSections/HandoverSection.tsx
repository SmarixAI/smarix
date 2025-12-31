'use client';

import { useEffect, useState, useMemo } from 'react';
import { CheckCircle } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type Handover = {
  id: string;
  item: string;
  currentOwner: string;
  newOwner?: string;
  priority: 'High' | 'Medium' | 'Low';
  status: 'Pending' | 'In Progress' | 'Completed';
  ktType: string[];
  lastUpdated: string;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= PRIORITY STYLES ================= */

const getPriorityBadge = (priority: Handover['priority'], darkMode: boolean): string => {
  if (darkMode) {
    return priority === 'High'
      ? 'bg-red-900/50 text-red-300'
      : priority === 'Medium'
      ? 'bg-yellow-900/50 text-yellow-300'
      : 'bg-green-900/50 text-green-300';
  }
  return priority === 'High'
    ? 'bg-red-100 text-red-700'
    : priority === 'Medium'
    ? 'bg-yellow-100 text-yellow-800'
    : 'bg-green-100 text-green-700';
};

/* ================= COMPONENT ================= */

export default function EmployeeHandoverSection({ employeeId, darkMode = false }: Props) {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [acknowledged, setAcknowledged] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  /* ================= LOAD HANDOVERS ================= */

  useEffect(() => {
    setLoading(true);
    const fetchData = async () => {
      try {
        const response = await fetch('/api/offboarding/handovers');
        if (!response.ok) {
          console.error('Failed to fetch handovers data');
          setLoading(false);
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) {
          console.log('No employees found in handovers data');
          setLoading(false);
          return;
        }

        console.log('Handovers - Looking for employeeId:', employeeId);
        console.log('Handovers - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        const employee =
          data.employees.find((e: any) => 
            e.employeeId === employeeId || 
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
          ) ?? data.employees[0];
        
        console.log('Handovers - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Handovers - Employee handovers:', employee?.handovers);

        setHandovers(employee.handovers ?? []);
      } catch (error) {
        console.error('Error fetching handovers data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY ================= */

  const summary = useMemo(() => {
    const total = handovers.length;
    const completed = handovers.filter(h => h.status === 'Completed').length;
    const pending = handovers.filter(h => h.status !== 'Completed').length;

    return { total, completed, pending };
  }, [handovers]);

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading handovers..." size="md" />;
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
            Your Handover Responsibilities
          </h3>
          <p className={`text-xs mt-1 ${
            darkMode ? "text-gray-400" : "text-slate-600"
          }`}>
            Items you must transfer before your last working day
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 px-5 py-4">
          <SummaryCard label="Total Items" value={summary.total} darkMode={darkMode} />
          <SummaryCard label="Completed" value={summary.completed} tone="green" darkMode={darkMode} />
          <SummaryCard label="Pending" value={summary.pending} tone="yellow" darkMode={darkMode} />
        </div>
      </div>

      {/* ================= HANDOVER LIST ================= */}
      <div className="space-y-4">
        {handovers.map(h => (
          <div
            key={h.id}
            className={`rounded-2xl border shadow-sm p-5 space-y-4 transition-colors duration-300 ${
              darkMode
                ? "border-gray-700 bg-gray-800"
                : "border-slate-200 bg-white"
            }`}
          >
            {/* TOP */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className={`text-base font-semibold ${
                  darkMode ? "text-gray-100" : "text-slate-900"
                }`}>
                  {h.item}
                </p>
                <p className={`text-sm mt-1 ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}>
                  Handover to{' '}
                  <span className={`font-semibold ${
                    darkMode ? "text-gray-200" : "text-slate-800"
                  }`}>
                    {h.newOwner || 'TBD'}
                  </span>
                </p>
              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${getPriorityBadge(h.priority, darkMode)}`}
              >
                {h.priority.toUpperCase()}
              </span>
            </div>

            {/* META */}
            <div className={`flex flex-wrap gap-4 text-xs ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>
              <div>
                <span className="font-semibold">Status:</span>{' '}
                <span
                  className={`font-semibold ${
                    h.status === 'Completed'
                      ? darkMode ? 'text-green-400' : 'text-green-700'
                      : h.status === 'In Progress'
                      ? darkMode ? 'text-yellow-400' : 'text-yellow-700'
                      : darkMode ? 'text-red-400' : 'text-red-600'
                  }`}
                >
                  {h.status}
                </span>
              </div>

              <div>
                <span className="font-semibold">KT Type:</span>{' '}
                {h.ktType.join(', ')}
              </div>

              <div className={darkMode ? "text-gray-500" : "text-slate-500"}>
                Last updated {h.lastUpdated}
              </div>
            </div>

            {/* EMPLOYEE ACTION */}
            <div className={`pt-4 border-t flex justify-between items-center ${
              darkMode ? "border-gray-700" : ""
            }`}>
              <p className={`text-xs ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Confirm you have completed your part of this handover
              </p>

              <button
                disabled={acknowledged[h.id]}
                onClick={() =>
                  setAcknowledged(prev => ({ ...prev, [h.id]: true }))
                }
                className={`
                  flex items-center gap-2 px-4 py-1.5 rounded-lg
                  text-xs font-semibold transition
                  ${
                    acknowledged[h.id]
                      ? 'bg-green-600 text-white'
                      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  }
                `}
              >
                <CheckCircle className="w-4 h-4" />
                {acknowledged[h.id] ? 'Acknowledged' : 'Mark as Done'}
              </button>
            </div>
          </div>
        ))}

        {handovers.length === 0 && (
          <div className={`text-sm italic ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            No handover items assigned to you.
          </div>
        )}
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
  tone?: 'green' | 'yellow' | 'slate';
  darkMode?: boolean;
}) {
  const getTones = (tone: string, darkMode: boolean): string => {
    if (darkMode) {
      return tone === 'green'
        ? 'bg-green-900/30 text-green-300'
        : tone === 'yellow'
        ? 'bg-yellow-900/30 text-yellow-300'
        : 'bg-gray-800 text-gray-100';
    }
    return tone === 'green'
      ? 'bg-green-50 text-green-800'
      : tone === 'yellow'
      ? 'bg-yellow-50 text-yellow-800'
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
