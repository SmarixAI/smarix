'use client';

import { useEffect, useState, useMemo } from 'react';
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

type HandoverSectionProps = {
  employeeId: string;
  darkMode?: boolean;
};

/* ================= COMPONENT ================= */

export default function HandoverSection({
  employeeId,
  darkMode = false
}: HandoverSectionProps) {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [updateCounter, setUpdateCounter] = useState(0); // Force re-render
  const [priorityFilter, setPriorityFilter] = useState<'All' | 'High' | 'Medium' | 'Low'>('All');
  const [loading, setLoading] = useState(true);

  // local UI-only state for scheduling
  const [schedule, setSchedule] = useState<Record<
    string,
    { owner: string; date: string; time: string }
  >>({});

  /* ================= LOAD HANDOVERS ================= */

  useEffect(() => {
    // Clear state when employeeId changes
    setHandovers([]);
    setUpdateCounter(0); // Reset update counter
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
          console.log('Manager Handover - No employees found in handovers data');
          setLoading(false);
          return;
        }

        console.log('Manager Handover - Looking for employeeId:', employeeId);
        console.log('Manager Handover - Available employeeIds:', data.employees.map((e: any) => e.employeeId || e.employee_id));
        
        // Try multiple matching strategies
        let employee = data.employees.find((e: any) => 
          e.employeeId === employeeId || 
          e.employee_id === employeeId ||
          String(e.employeeId) === String(employeeId) ||
          String(e.employee_id) === String(employeeId)
        );

        if (!employee) {
          console.log('Manager Handover - Employee not found, using first employee');
          employee = data.employees[0];
        }

        console.log('Manager Handover - Found employee:', employee ? { employeeId: employee.employeeId || employee.employee_id, name: employee.name } : 'NOT FOUND');
        console.log('Manager Handover - Employee handovers:', employee?.handovers);

        // Set handovers if employee found (removed strict check to allow fallback)
        if (employee) {
          setHandovers(employee.handovers ?? []);
        }
      } catch (error) {
        console.error('Error fetching handovers data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  /* ================= SUMMARY (NEW) ================= */

  const summary = useMemo(() => {
    const total = handovers.length;
    const completed = handovers.filter(h => h.status === 'Completed').length;
    const inProgress = handovers.filter(h => h.status === 'In Progress').length;
    const pending = handovers.filter(h => h.status === 'Pending').length;
    const assigned = handovers.filter(
      h => h.newOwner && h.newOwner.trim().length > 0
    ).length;
    const yetToAssign = total - assigned;

    return {
      total,
      completed,
      inProgress,
      pending,
      assigned,
      yetToAssign
    };
  }, [handovers]);

  // Filter handovers based on priority
  const filteredHandovers = useMemo(() => {
    if (priorityFilter === 'All') return handovers;
    return handovers.filter(h => h.priority === priorityFilter);
  }, [handovers, priorityFilter]);

  /* ================= UPDATE HELPERS ================= */

  const updateHandover = async (
    id: string,
    updates: Partial<Handover>
  ) => {
    // Store old priority for potential revert
    const oldPriority = updates.priority ? handovers.find(h => h.id === id)?.priority : undefined;

    // Update local state immediately using functional form
    setHandovers(prev => prev.map(h =>
      h.id === id ? { ...h, ...updates } : h
    ));
    // Force re-render
    if (updates.priority) {
      setUpdateCounter(prev => prev + 1);
    }

    // If priority is being updated, persist to backend
    if (updates.priority) {
      try {
        const response = await fetch('/api/offboarding/handovers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            employeeId: employeeId,
            handoverId: id,
            priority: updates.priority,
          }),
        });

        if (!response.ok) {
          console.error('Failed to update handover priority');
          // Revert on error using functional form
          if (oldPriority) {
            setHandovers(prev => prev.map(h =>
              h.id === id ? { ...h, priority: oldPriority } : h
            ));
          }
        }
      } catch (error) {
        console.error('Error updating handover priority:', error);
        // Revert on error using functional form
        if (oldPriority) {
          setHandovers(prev => prev.map(h =>
            h.id === id ? { ...h, priority: oldPriority } : h
          ));
        }
      }
    }
  };

  const updateSchedule = (
    id: string,
    key: 'owner' | 'date' | 'time',
    value: string
  ) => {
    setSchedule(prev => ({
      ...prev,
      [id]: {
        ...prev[id],
        [key]: value
      }
    }));
  };

  const scheduleMeeting = (h: Handover) => {
    const s = schedule[h.id];
    console.log('📅 Scheduling KT meeting', {
      item: h.item,
      from: h.currentOwner,
      to: s?.owner || h.newOwner,
      date: s?.date,
      time: s?.time
    });

    alert('KT Meeting scheduled (mock)');
  };

  const getPriorityStyles = (priority: Handover['priority'], darkMode: boolean): string => {
    if (darkMode) {
      return priority === 'High'
        ? 'bg-red-900/30 text-red-300 border-red-700 focus:ring-red-400'
        : priority === 'Medium'
        ? 'bg-yellow-900/30 text-yellow-300 border-yellow-700 focus:ring-yellow-400'
        : 'bg-green-900/30 text-green-300 border-green-700 focus:ring-green-400';
    }
    return priority === 'High'
      ? 'bg-red-50 text-red-700 border-red-300 focus:ring-red-400'
      : priority === 'Medium'
      ? 'bg-yellow-50 text-yellow-800 border-yellow-300 focus:ring-yellow-400'
      : 'bg-green-50 text-green-700 border-green-300 focus:ring-green-400';
  };

  /* ================= UI ================= */

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading handovers..." size="md" />;
  }

  return (
    <div className="space-y-4">

      {/* ================= HANDOVER SUMMARY ================= */}
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
            Handover Summary
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
              ? "border-green-700 bg-gradient-to-br from-green-900/30 to-green-900/50"
              : "border-green-200 bg-gradient-to-br from-green-50 to-green-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-green-400" : "text-green-700"
            }`}>Completed</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-green-300" : "text-green-800"
            }`}>
              {summary.completed}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-yellow-700 bg-gradient-to-br from-yellow-900/30 to-yellow-900/50"
              : "border-yellow-200 bg-gradient-to-br from-yellow-50 to-yellow-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-yellow-400" : "text-yellow-700"
            }`}>In Progress</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-yellow-300" : "text-yellow-800"
            }`}>
              {summary.inProgress}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-red-700 bg-gradient-to-br from-red-900/30 to-red-900/50"
              : "border-red-200 bg-gradient-to-br from-red-50 to-red-100"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-red-400" : "text-red-700"
            }`}>Pending</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-red-300" : "text-red-800"
            }`}>
              {summary.pending}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-indigo-700 bg-gradient-to-br from-indigo-900/30 to-purple-900/30"
              : "border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-indigo-400" : "text-indigo-700"
            }`}>Assigned</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-indigo-300" : "text-indigo-800"
            }`}>
              {summary.assigned}
            </p>
          </div>

          <div className={`rounded-xl border-2 px-3 py-2 shadow-sm transition-colors duration-300 ${
            darkMode
              ? "border-gray-600 bg-gradient-to-br from-gray-700 to-gray-800"
              : "border-slate-300 bg-gradient-to-br from-slate-100 to-slate-200"
          }`}>
            <p className={`text-[10px] font-bold mb-0.5 ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>To Assign</p>
            <p className={`text-xl font-extrabold ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>
              {summary.yetToAssign}
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
        <div className="flex items-center gap-3">
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
        Feature-Level Handovers
      </h2>

      {/* ================= HANDOVER LIST ================= */}
      <div className="space-y-4">
        {filteredHandovers.length > 0 ? (
          filteredHandovers.map(h => (
          <div
            key={h.id}
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
                  {h.item}
                </p>
                <p className={`text-sm mt-1 ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}>
                  {h.currentOwner} →{' '}
                  <span className={`font-semibold ${
                    darkMode ? "text-gray-200" : "text-slate-800"
                  }`}>
                    {h.newOwner || 'Unassigned'}
                  </span>
                </p>
              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  h.priority === 'High'
                    ? darkMode
                      ? 'bg-red-900/50 text-red-300'
                      : 'bg-red-100 text-red-700'
                    : h.priority === 'Medium'
                    ? darkMode
                      ? 'bg-yellow-900/50 text-yellow-300'
                      : 'bg-yellow-100 text-yellow-800'
                    : darkMode
                      ? 'bg-green-900/50 text-green-300'
                      : 'bg-green-100 text-green-700'
                }`}
              >
                {h.priority.toUpperCase()}
              </span>
            </div>

            {/* META INFO */}
            <div className={`flex flex-wrap gap-4 text-xs ${
              darkMode ? "text-gray-400" : "text-slate-700"
            }`}>
              <div>
                <span className="font-semibold">Status:</span>{' '}
                <span
                  className={`font-semibold ${
                    h.status === 'Pending'
                      ? darkMode ? 'text-red-400' : 'text-red-600'
                      : h.status === 'In Progress'
                      ? darkMode ? 'text-yellow-400' : 'text-yellow-700'
                      : darkMode ? 'text-green-400' : 'text-green-700'
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

            {/* ================= HANDOVER CONTROLS ================= */}
            <div className={`pt-4 border-t ${
              darkMode ? "border-gray-700" : "border-slate-200"
            }`}>
              <div className="flex flex-wrap items-center gap-3">

                <select
                  key={`${h.id}-${h.priority}-${updateCounter}`}
                  value={h.priority}
                  onChange={e =>
                    updateHandover(h.id, {
                      priority: e.target.value as Handover['priority']
                    })
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs font-semibold border
                    focus:outline-none focus:ring-2 focus:ring-offset-1
                    ${getPriorityStyles(h.priority, darkMode)}
                  `}
                >
                  <option value="High">High Priority</option>
                  <option value="Medium">Medium Priority</option>
                  <option value="Low">Low Priority</option>
                </select>

                <select
                  value={schedule[h.id]?.owner || h.newOwner || ''}
                  onChange={e =>
                    updateSchedule(h.id, 'owner', e.target.value)
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs font-medium border
                    focus:outline-none focus:ring-2
                    ${darkMode
                      ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                      : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
                    }
                  `}
                >
                  <option value="">Select New Owner</option>
                  <option value="Ankit Sharma">Ankit Sharma</option>
                  <option value="Neha Gupta">Neha Gupta</option>
                  <option value="Rohit Mehta">Rohit Mehta</option>
                </select>

                <input
                  type="date"
                  value={schedule[h.id]?.date || ''}
                  onChange={e =>
                    updateSchedule(h.id, 'date', e.target.value)
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs border
                    focus:outline-none focus:ring-2
                    ${darkMode
                      ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                      : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
                    }
                  `}
                />

                <input
                  type="time"
                  value={schedule[h.id]?.time || ''}
                  onChange={e =>
                    updateSchedule(h.id, 'time', e.target.value)
                  }
                  className={`
                    px-3 py-1.5 rounded-lg text-xs border
                    focus:outline-none focus:ring-2
                    ${darkMode
                      ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                      : "border-slate-300 bg-white text-slate-900 focus:ring-indigo-500"
                    }
                  `}
                />

                <button
                  onClick={() => scheduleMeeting(h)}
                  className={`
                    ml-auto px-4 py-1.5 rounded-lg text-xs font-semibold
                    text-white shadow-sm transition
                    ${darkMode
                      ? "bg-indigo-600 hover:bg-indigo-700"
                      : "bg-indigo-600 hover:bg-indigo-700"
                    }
                  `}
                >
                  Schedule KT Meeting
                </button>
              </div>
            </div>
          </div>
        ))
        ) : (
          <div className={`text-sm italic ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            {handovers.length === 0 
              ? 'No handover items for this employee.'
              : 'No handovers match the current filter.'}
          </div>
        )}
      </div>
    </div>
  );
}
