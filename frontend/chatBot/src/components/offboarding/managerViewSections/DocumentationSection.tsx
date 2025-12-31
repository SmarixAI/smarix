'use client';

import { useEffect, useState, useMemo } from 'react';
import Loader from '../Loader';

/* ================= TYPES ================= */

type DocStatus = 'Missing' | 'Partial' | 'Complete';
type DocPriority = 'High' | 'Medium' | 'Low';

type DocumentItem = {
  id: string;
  name: string;
  status: DocStatus;
  priority: DocPriority;
  owner: string;
  aiFollowUp: boolean;
  lastUpdated: string;
};

type DocumentationSectionProps = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= STYLE MAPS ================= */

const getStatusStyles = (status: DocStatus, darkMode: boolean): string => {
  if (darkMode) {
    return status === 'Missing'
      ? 'bg-red-900/30 text-red-300 border-red-700'
      : status === 'Partial'
      ? 'bg-yellow-900/30 text-yellow-300 border-yellow-700'
      : 'bg-green-900/30 text-green-300 border-green-700';
  }
  return status === 'Missing'
    ? 'bg-red-100 text-red-700 border-red-300'
    : status === 'Partial'
    ? 'bg-yellow-100 text-yellow-800 border-yellow-300'
    : 'bg-green-100 text-green-700 border-green-300';
};

const getPriorityStyles = (priority: DocPriority, darkMode: boolean): string => {
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

export default function DocumentationSection({
  employeeId,
  darkMode = false
}: DocumentationSectionProps) {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [updateCounter, setUpdateCounter] = useState(0); // Force re-render
  const [statusFilter, setStatusFilter] = useState<'All' | DocStatus>('All');
  const [priorityFilter, setPriorityFilter] = useState<'All' | DocPriority>('All');
  const [loading, setLoading] = useState(true);

  /* ================= LOAD DATA ================= */

  useEffect(() => {
    // Clear state when employeeId changes
    setDocs([]);
    setUpdateCounter(0); // Reset update counter
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
          console.log('Manager Documentation - No employees found in documents data');
          setLoading(false);
          return;
        }

        console.log('Manager Documentation - Looking for employeeId:', employeeId);
        console.log('Manager Documentation - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        let employee = data.employees.find((e: any) => 
          e.employeeId === employeeId || 
          e.employee_id === employeeId ||
          String(e.employeeId) === String(employeeId) ||
          String(e.employee_id) === String(employeeId)
        );

        if (!employee) {
          console.log('Manager Documentation - Employee not found, using first employee');
          employee = data.employees[0];
        }

        console.log('Manager Documentation - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Manager Documentation - Employee documents:', employee?.documents);

        // Set documents if employee found (removed strict check to allow fallback)
        if (employee) {
          setDocs(employee.documents ?? []);
        }
      } catch (error) {
        console.error('Error fetching documents data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY (NEW) ================= */

  const summary = useMemo(() => {
    const total = docs.length;
    const missing = docs.filter(d => d.status === 'Missing').length;
    const partial = docs.filter(d => d.status === 'Partial').length;
    const complete = docs.filter(d => d.status === 'Complete').length;
    const aiFollowUps = docs.filter(d => d.aiFollowUp).length;

    const quality =
      total === 0
        ? 0
        : Math.round(
            ((complete * 100 + partial * 50) / (total * 100)) * 100
          );

    return {
      total,
      missing,
      partial,
      complete,
      aiFollowUps,
      quality
    };
  }, [docs]);

  // Filter documents based on status and priority
  const filteredDocs = useMemo(() => {
    let filtered = docs;
    if (statusFilter !== 'All') {
      filtered = filtered.filter(d => d.status === statusFilter);
    }
    if (priorityFilter !== 'All') {
      filtered = filtered.filter(d => d.priority === priorityFilter);
    }
    return filtered;
  }, [docs, statusFilter, priorityFilter]);

  /* ================= UPDATE HELPERS ================= */

  const updateDoc = async (
    id: string,
    updates: Partial<DocumentItem>
  ) => {
    // Store old values for potential revert
    const oldPriority = updates.priority ? docs.find(d => d.id === id)?.priority : undefined;
    const oldStatus = updates.status ? docs.find(d => d.id === id)?.status : undefined;

    // Update local state immediately using functional form
    setDocs(prev => prev.map(d =>
      d.id === id ? { ...d, ...updates } : d
    ));
    // Force re-render
    if (updates.priority || updates.status) {
      setUpdateCounter(prev => prev + 1);
    }

    // If priority or status is being updated, persist to backend
    if (updates.priority || updates.status) {
      try {
        const response = await fetch('/api/offboarding/documents', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            employeeId: employeeId,
            documentId: id,
            priority: updates.priority,
            status: updates.status,
          }),
        });

        if (!response.ok) {
          console.error('Failed to update document');
          // Revert on error using functional form
          setDocs(prev => prev.map(d => {
            if (d.id === id) {
              const reverted: Partial<DocumentItem> = {};
              if (oldPriority !== undefined) reverted.priority = oldPriority;
              if (oldStatus !== undefined) reverted.status = oldStatus;
              return { ...d, ...reverted };
            }
            return d;
          }));
        }
      } catch (error) {
        console.error('Error updating document:', error);
        // Revert on error using functional form
        setDocs(prev => prev.map(d => {
          if (d.id === id) {
            const reverted: Partial<DocumentItem> = {};
            if (oldPriority !== undefined) reverted.priority = oldPriority;
            if (oldStatus !== undefined) reverted.status = oldStatus;
            return { ...d, ...reverted };
          }
          return d;
        }));
      }
    }
  };

  const askAI = (doc: DocumentItem) => {
    console.log('🤖 Ask AI for:', doc.name);
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading documents..." size="md" />;
  }

  return (
    <div className="space-y-4">

      {/* ================= SUMMARY SECTION ================= */}
      <div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/80"
          : "border-slate-200/50 bg-white/80"
      }`}>
        <div className={`px-4 py-2.5 border-b ${
          darkMode
            ? "border-gray-700 bg-gradient-to-r from-indigo-900/50 to-purple-900/50"
            : "border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50"
        }`}>
          <h3 className={`font-bold text-sm ${
            darkMode
              ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
              : "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent"
          }`}>
            Documentation Summary
          </h3>
        </div>

        <div className="grid grid-cols-6 gap-2 px-4 py-3">
          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-gray-700 bg-gradient-to-br from-gray-800 to-gray-900"
              : "border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>Total</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>
              {summary.total}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-red-700 bg-gradient-to-br from-red-900/30 to-red-900/50"
              : "border-red-200 bg-gradient-to-br from-red-50 to-red-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-red-400" : "text-red-700"
            }`}>Missing</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-red-300" : "text-red-800"
            }`}>
              {summary.missing}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-yellow-700 bg-gradient-to-br from-yellow-900/30 to-yellow-900/50"
              : "border-yellow-200 bg-gradient-to-br from-yellow-50 to-yellow-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-yellow-400" : "text-yellow-700"
            }`}>Partial</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-yellow-300" : "text-yellow-800"
            }`}>
              {summary.partial}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-green-700 bg-gradient-to-br from-green-900/30 to-green-900/50"
              : "border-green-200 bg-gradient-to-br from-green-50 to-green-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-green-400" : "text-green-700"
            }`}>Complete</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-green-300" : "text-green-800"
            }`}>
              {summary.complete}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-indigo-700 bg-gradient-to-br from-indigo-900/30 to-purple-900/30"
              : "border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-indigo-400" : "text-indigo-700"
            }`}>AI Follow-ups</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-indigo-300" : "text-indigo-800"
            }`}>
              {summary.aiFollowUps}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-gray-600 bg-gradient-to-br from-gray-700 to-gray-800"
              : "border-slate-300 bg-gradient-to-br from-slate-100 to-slate-200"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>Quality</p>
            <p
              className={`text-xl font-extrabold ${
                summary.quality >= 80
                  ? darkMode ? 'text-green-300' : 'text-green-700'
                  : summary.quality >= 50
                  ? darkMode ? 'text-yellow-300' : 'text-yellow-700'
                  : darkMode ? 'text-red-300' : 'text-red-700'
              }`}
            >
              {summary.quality}%
            </p>
          </div>
        </div>
      </div>

      {/* ================= FILTERS ================= */}
      <div className={`rounded-2xl border-2 backdrop-blur-lg shadow-lg p-3 transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/80"
          : "border-slate-200/50 bg-white/80"
      }`}>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className={`text-xs font-semibold ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>Status:</label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as any)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-semibold border-2
                focus:outline-none focus:ring-2 focus:border-indigo-500
                transition-all duration-200
                ${darkMode
                  ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                  : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
                }
              `}
            >
              <option value="All">All</option>
              <option value="Missing">Missing</option>
              <option value="Partial">Partial</option>
              <option value="Complete">Complete</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className={`text-xs font-semibold ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value as any)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-semibold border-2
                focus:outline-none focus:ring-2 focus:border-indigo-500
                transition-all duration-200
                ${darkMode
                  ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                  : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
                }
              `}
            >
              <option value="All">All</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* ================= SECTION TITLE ================= */}
      <h2 className={`text-sm font-bold uppercase tracking-wide ${
        darkMode ? "text-gray-300" : "text-slate-700"
      }`}>
        Mandatory Documents
      </h2>

      {/* ================= DOCUMENT LIST ================= */}
      <div className="space-y-4">
        {filteredDocs.length > 0 ? (
          filteredDocs.map(d => (
          <div
            key={d.id}
            className={`rounded-2xl border shadow-sm p-5 space-y-4 transition-colors duration-300 ${
              darkMode
                ? "border-gray-700 bg-gray-800"
                : "border-slate-200 bg-white"
            }`}
          >
            {/* TOP ROW */}
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
                className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusStyles(d.status, darkMode)}`}
              >
                {d.status.toUpperCase()}
              </span>
            </div>

            {/* META INFO */}
            <div className={`flex flex-wrap gap-4 text-xs ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>
              <div>
                <span className="font-semibold">Priority:</span>{' '}
                <span className={`font-semibold ${getPriorityStyles(d.priority, darkMode)}`}>
                  {d.priority}
                </span>
              </div>

              <div>
                <span className="font-semibold">Last Updated:</span>{' '}
                <span className={darkMode ? "text-gray-500" : "text-slate-600"}>
                  {d.lastUpdated}
                </span>
              </div>

              {d.aiFollowUp && (
                <div className={darkMode ? "text-indigo-400 font-semibold" : "text-indigo-700 font-semibold"}>
                  🤖 AI follow-up required
                </div>
              )}
            </div>

            {/* ================= ACTION ROW ================= */}
            <div className={`pt-4 border-t rounded-b-xl -mx-5 px-5 pb-1 transition-colors duration-300 ${
              darkMode
                ? "border-gray-700 bg-gray-900/50"
                : "border-slate-200 bg-slate-50"
            }`}>
              <div className="flex flex-wrap items-center gap-3">

                {/* STATUS */}
                <select
                  key={`${d.id}-status-${d.status}-${updateCounter}`}
                  value={d.status}
                  onChange={e =>
                    updateDoc(d.id, {
                      status: e.target.value as DocStatus
                    })
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs font-bold border-2 shadow-sm
                    focus:outline-none focus:ring-2 focus:ring-offset-1
                    ${getStatusStyles(d.status, darkMode)}
                    ${darkMode ? 'focus:ring-offset-gray-800' : 'focus:ring-offset-1'}
                  `}
                >
                  <option value="Missing">Missing</option>
                  <option value="Partial">Partial</option>
                  <option value="Complete">Complete</option>
                </select>

                {/* PRIORITY */}
                <select
                  key={`${d.id}-priority-${d.priority}-${updateCounter}`}
                  value={d.priority}
                  onChange={e =>
                    updateDoc(d.id, {
                      priority: e.target.value as DocPriority
                    })
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs font-semibold border-2 shadow-sm
                    focus:outline-none focus:ring-2
                    ${darkMode
                      ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                      : "border-slate-400 bg-white text-slate-900 focus:ring-indigo-500"
                    }
                  `}
                >
                  <option value="High">High Priority</option>
                  <option value="Medium">Medium Priority</option>
                  <option value="Low">Low Priority</option>
                </select>

                
                {/* PRIMARY CTA */}
                <button
                  onClick={() => askAI(d)}
                  disabled={d.status === 'Complete'}
                  className={`
                    ml-auto
                    px-4 py-2
                    rounded-lg
                    text-xs font-bold
                    tracking-wide
                    shadow-md
                    transition
                    ${
                      d.status === 'Complete'
                        ? darkMode
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : 'bg-slate-300 text-slate-600 cursor-not-allowed'
                        : darkMode
                          ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                          : 'bg-indigo-700 hover:bg-indigo-800 text-white'
                    }
                  `}
                >
                  Ask AI to Collect Info
                </button>
              </div>
            </div>
          </div>
        ))
        ) : (
          <div className={`text-sm italic ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            {docs.length === 0 
              ? 'No documentation items for this employee.'
              : 'No documents match the current filters.'}
          </div>
        )}
      </div>
    </div>
  );
}
