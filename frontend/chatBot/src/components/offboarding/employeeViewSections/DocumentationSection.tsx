'use client';

import { useEffect, useState, useMemo } from 'react';
import { CheckCircle } from 'lucide-react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type DocStatus = 'Missing' | 'Partial' | 'Complete';

type DocumentItem = {
  id: string;
  name: string;
  status: DocStatus;
  priority: 'High' | 'Medium' | 'Low';
  owner: string;
  aiFollowUp: boolean;
  lastUpdated: string;
};

type Props = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= STYLE MAPS ================= */

const getStatusBadge = (status: DocStatus, darkMode: boolean): string => {
  if (darkMode) {
    return status === 'Missing'
      ? 'bg-red-900/50 text-red-300'
      : status === 'Partial'
      ? 'bg-yellow-900/50 text-yellow-300'
      : 'bg-green-900/50 text-green-300';
  }
  return status === 'Missing'
    ? 'bg-red-100 text-red-700'
    : status === 'Partial'
    ? 'bg-yellow-100 text-yellow-800'
    : 'bg-green-100 text-green-700';
};

const getPriorityText = (priority: 'High' | 'Medium' | 'Low', darkMode: boolean): string => {
  if (darkMode) {
    return priority === 'High'
      ? 'text-red-300'
      : priority === 'Medium'
      ? 'text-yellow-300'
      : 'text-green-300';
  }
  return priority === 'High'
    ? 'text-red-700'
    : priority === 'Medium'
    ? 'text-yellow-700'
    : 'text-green-700';
};

/* ================= COMPONENT ================= */

export default function EmployeeDocumentationSection({ employeeId, darkMode = false }: Props) {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [acknowledged, setAcknowledged] = useState(false);

  /* ================= LOAD DATA ================= */

  useEffect(() => {
    setLoading(true);
    const fetchData = async () => {
      try {
        const response = await fetch('/api/offboarding/documents');
        if (!response.ok) {
          console.error('Failed to fetch documents data');
          setLoading(false);
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) {
          console.log('No employees found in documents data');
          setLoading(false);
          return;
        }

        console.log('Documents - Looking for employeeId:', employeeId);
        console.log('Documents - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        const employee =
          data.employees.find((e: any) => 
            e.employeeId === employeeId || 
            e.employee_id === employeeId ||
            String(e.employeeId) === String(employeeId) ||
            String(e.employee_id) === String(employeeId)
          ) ?? data.employees[0];
        
        console.log('Documents - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Documents - Employee documents:', employee?.documents);

        setDocs(employee.documents ?? []);
      } catch (error) {
        console.error('Error fetching documents data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY ================= */

  const summary = useMemo(() => {
    const total = docs.length;
    const missing = docs.filter(d => d.status === 'Missing').length;
    const partial = docs.filter(d => d.status === 'Partial').length;
    const complete = docs.filter(d => d.status === 'Complete').length;

    return { total, missing, partial, complete };
  }, [docs]);

  /* ================= UPDATE (EMPLOYEE-SAFE) ================= */

  const updateStatus = (id: string, status: DocStatus) => {
    setDocs(prev =>
      prev.map(d =>
        d.id === id ? { ...d, status } : d
      )
    );
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading documents..." size="md" />;
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
            Your Documentation Checklist
          </h3>
          <p className={`text-xs mt-1 ${
            darkMode ? "text-gray-400" : "text-slate-600"
          }`}>
            Documents you must complete before your last working day
          </p>
        </div>

        <div className="grid grid-cols-4 gap-4 px-5 py-4">
          <SummaryCard label="Total Docs" value={summary.total} darkMode={darkMode} />
          <SummaryCard label="Missing" value={summary.missing} tone="red" darkMode={darkMode} />
          <SummaryCard label="Partial" value={summary.partial} tone="yellow" darkMode={darkMode} />
          <SummaryCard label="Complete" value={summary.complete} tone="green" darkMode={darkMode} />
        </div>
      </div>

      {/* ================= DOCUMENT LIST ================= */}
      <div className="space-y-4">
        {docs.map(d => (
          <div
            key={d.id}
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
                  {d.name}
                </p>
                <p className={`text-sm mt-1 ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}>
                  Owner:{' '}
                  <span className={`font-semibold ${
                    darkMode ? "text-gray-200" : "text-slate-800"
                  }`}>
                    {d.owner}
                  </span>
                </p>
              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusBadge(d.status, darkMode)}`}
              >
                {d.status.toUpperCase()}
              </span>
            </div>

            {/* META */}
            <div className={`flex flex-wrap gap-4 text-xs ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>
              <div>
                <span className="font-semibold">Priority:</span>{' '}
                <span className={`font-semibold ${getPriorityText(d.priority, darkMode)}`}>
                  {d.priority}
                </span>
              </div>

              <div className={darkMode ? "text-gray-500" : "text-slate-500"}>
                Last updated {d.lastUpdated}
              </div>

              {d.aiFollowUp && (
                <div className={darkMode ? "text-indigo-400 font-semibold" : "text-indigo-700 font-semibold"}>
                  🤖 AI follow-up required
                </div>
              )}
            </div>

            {/* EMPLOYEE ACTION */}
            <div className={`pt-4 border-t flex items-center justify-between ${
              darkMode ? "border-gray-700" : ""
            }`}>
              <p className={`text-xs ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Update your progress for this document
              </p>

              <select
                value={d.status}
                onChange={e =>
                  updateStatus(d.id, e.target.value as DocStatus)
                }
                className={`
                  px-3 py-1.5 rounded-lg text-xs font-bold border
                  focus:outline-none focus:ring-2
                  ${d.status === 'Missing'
                    ? darkMode
                      ? 'bg-red-900/30 text-red-300 border-red-700 focus:ring-red-400'
                      : 'bg-red-100 text-red-800 border-red-400 focus:ring-red-400'
                    : d.status === 'Partial'
                    ? darkMode
                      ? 'bg-yellow-900/30 text-yellow-300 border-yellow-700 focus:ring-yellow-400'
                      : 'bg-yellow-100 text-yellow-900 border-yellow-400 focus:ring-yellow-400'
                    : darkMode
                      ? 'bg-green-900/30 text-green-300 border-green-700 focus:ring-green-400'
                      : 'bg-green-100 text-green-800 border-green-400 focus:ring-green-400'
                  }
                `}
              >
                <option value="Missing">Missing</option>
                <option value="Partial">Partial</option>
                <option value="Complete">Complete</option>
              </select>
            </div>
          </div>
        ))}

        {docs.length === 0 && (
          <div className={`text-sm italic ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            No documentation items assigned to you.
          </div>
        )}
      </div>

      {/* ================= ACKNOWLEDGEMENT ================= */}
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
            Confirm that you will complete all required documentation
          </p>
        </div>

        <button
          disabled={acknowledged}
          onClick={() => setAcknowledged(true)}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-xl
            text-sm font-semibold transition
            ${
              acknowledged
                ? 'bg-green-600 text-white'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }
          `}
        >
          <CheckCircle className="w-4 h-4" />
          {acknowledged ? 'Acknowledged' : 'I Acknowledge'}
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
