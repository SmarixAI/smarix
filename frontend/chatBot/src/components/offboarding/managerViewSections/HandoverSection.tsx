'use client';

import { useEffect, useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, FileText, HelpCircle, ExternalLink, User } from 'lucide-react';
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
  description?: string;
  questions?: string[];
  reference?: string;
  suggested_recipient?: string;
  suggested_recipient_reason?: string;
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
  
  // Expanded handover IDs
  const [expandedHandoverIds, setExpandedHandoverIds] = useState<Set<string>>(new Set());

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
          String(e.employee_id) === String(employeeId) ||
          e.name === employeeId ||
          e.employee_name === employeeId
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
    <div className="space-y-3 p-4">

      {/* ================= HANDOVER SUMMARY - REMOVED ================= */}

      {/* ================= FILTERS ================= */}
      <div className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 px-4 py-3 transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/50"
          : ""
      }`}>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className={`text-xs font-medium ${
              darkMode ? "text-gray-300" : "text-[#0E1B2E]/70"
            }`}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value as any)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium border
                focus:outline-none focus:ring-1 focus:border-[#0E1B2E]/30
                transition-all duration-200
                ${darkMode
                  ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                  : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
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
      <h2 className={`text-base font-semibold uppercase tracking-wide mb-4 text-[#0E1B2E] ${
        darkMode ? "text-gray-300" : ""
      }`}>
        Feature-Level Handovers
      </h2>

      {/* ================= HANDOVER LIST ================= */}
      <div className="space-y-3">
        {filteredHandovers.length > 0 ? (
          filteredHandovers.map(h => {
            const isExpanded = expandedHandoverIds.has(h.id);
            const hasDetails = h.description || h.questions?.length || h.reference || h.suggested_recipient_reason;
            
            return (
              <div
                key={h.id}
                className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 overflow-hidden transition-colors duration-300 ${
                  darkMode
                    ? "border-gray-700 bg-gray-800/50"
                    : ""
                }`}
              >
              {/* TOP ROW */}
              <div 
                className={`flex items-start justify-between gap-4 p-4 cursor-pointer transition-colors ${
                  hasDetails ? (darkMode ? "hover:bg-gray-800/70" : "hover:bg-white/50") : ""
                } ${isExpanded ? (darkMode ? "bg-gray-800/30" : "bg-white/40") : ""}`}
                onClick={() => hasDetails && setExpandedHandoverIds(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(h.id)) {
                    newSet.delete(h.id);
                  } else {
                    newSet.add(h.id);
                  }
                  return newSet;
                })}
              >
                <div className="flex-1 flex items-start gap-2">
                  {hasDetails && (
                    <div className="mt-0.5">
                      {isExpanded ? (
                        <ChevronUp className={`w-4 h-4 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                      ) : (
                        <ChevronDown className={`w-4 h-4 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                      )}
                    </div>
                  )}
                  <div>
                    <p className={`text-sm font-medium ${
                      darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                    }`}>
                      {h.item}
                    </p>
                <p className={`text-xs mt-0.5 ${
                  darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
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
            </div>

            {/* META INFO */}
            <div className={`px-4 flex flex-wrap gap-3 text-xs ${
              darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
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

            {/* EXPANDED DETAILS */}
            {isExpanded && hasDetails && (
              <div className={`px-4 pb-3 border-t border-[#0E1B2E]/10 ${
                darkMode ? "bg-gray-800/30" : "bg-white/20"
              }`}>
                <div className="space-y-3 pt-3">
                  {/* DESCRIPTION */}
                  {h.description && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <FileText className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          Description
                        </h4>
                      </div>
                      <div className={`text-xs ml-5 whitespace-pre-wrap ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                        {h.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
                      </div>
                    </div>
                  )}

                  {/* QUESTIONS */}
                  {h.questions && h.questions.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <HelpCircle className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          Questions ({h.questions.length})
                        </h4>
                      </div>
                      <ul className="ml-5 space-y-1.5">
                        {h.questions.map((q, idx) => (
                          <li key={idx} className={`text-xs flex items-start gap-2 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                            <span className="mt-0.5">{idx + 1}.</span>
                            <span>{q}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* REFERENCE */}
                  {h.reference && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <ExternalLink className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          References
                        </h4>
                      </div>
                      <div className={`text-xs ml-5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                        {h.reference.split(', ').map((ref, idx) => (
                          <div key={idx} className="font-mono">{ref}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SUGGESTED RECIPIENT */}
                  {h.suggested_recipient && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <User className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          Suggested Recipient
                        </h4>
                      </div>
                      <div className={`text-xs ml-5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                        <div className="font-medium">{h.suggested_recipient}</div>
                        {h.suggested_recipient_reason && (
                          <div className="mt-1">{h.suggested_recipient_reason}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ================= HANDOVER CONTROLS ================= */}
            <div className={`pt-3 border-t border-[#0E1B2E]/10 ${
              darkMode ? "border-gray-700" : ""
            }`}>
              <div className="flex flex-wrap items-center gap-2">

                <select
                  key={`${h.id}-${h.priority}-${updateCounter}`}
                  value={h.priority}
                  onChange={e =>
                    updateHandover(h.id, {
                      priority: e.target.value as Handover['priority']
                    })
                  }
                  className={`
                    px-2.5 py-1 rounded-lg text-xs font-medium border
                    focus:outline-none focus:ring-1 focus:ring-offset-0
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
                    px-2.5 py-1 rounded-lg text-xs font-medium border
                    focus:outline-none focus:ring-1
                    ${darkMode
                      ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                      : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
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
                    px-2.5 py-1 rounded-lg text-xs border
                    focus:outline-none focus:ring-1
                    ${darkMode
                      ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                      : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
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
                    px-2.5 py-1 rounded-lg text-xs border
                    focus:outline-none focus:ring-1
                    ${darkMode
                      ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                      : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
                    }
                  `}
                />

                <button
                  onClick={() => scheduleMeeting(h)}
                  className={`
                    ml-auto px-3 py-1.5 rounded-lg text-xs font-medium
                    text-white shadow-sm transition
                    ${darkMode
                      ? "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
                      : "bg-[#0E1B2E] hover:bg-[#1a2f4d]"
                    }
                  `}
                >
                  Schedule KT Meeting
                </button>
              </div>
            </div>
          </div>
            );
          })
        ) : (
          <div className={`text-xs italic px-4 py-3 ${
            darkMode ? "text-gray-400" : "text-[#0E1B2E]/50"
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
