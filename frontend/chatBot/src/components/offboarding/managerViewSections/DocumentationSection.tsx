'use client';

import { useEffect, useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, FileText, HelpCircle, ExternalLink } from 'lucide-react';
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
  description?: string;
  questions?: string[];
  reference?: string;
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
  
  // Expanded document IDs
  const [expandedDocIds, setExpandedDocIds] = useState<Set<string>>(new Set());

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
          String(e.employee_id) === String(employeeId) ||
          e.name === employeeId ||
          e.employee_name === employeeId
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
    <div className="space-y-3 p-4">

      {/* ================= SUMMARY SECTION - REMOVED ================= */}

      {/* ================= FILTERS ================= */}
      <div className={`rounded-xl border bg-white/35 backdrop-blur-xl border-white/25 shadow-md shadow-black/5 px-4 py-3 transition-colors duration-300 ${
        darkMode
          ? "border-gray-700 bg-gray-800/50"
          : ""
      }`}>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className={`text-xs font-medium ${
              darkMode ? "text-gray-300" : "text-[#0E1B2E]/70"
            }`}>Status:</label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as any)}
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
              <option value="Missing">Missing</option>
              <option value="Partial">Partial</option>
              <option value="Complete">Complete</option>
            </select>
          </div>

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
        Mandatory Documents
      </h2>

      {/* ================= DOCUMENT LIST ================= */}
      <div className="space-y-3">
        {filteredDocs.length > 0 ? (
          filteredDocs.map(d => {
            const isExpanded = expandedDocIds.has(d.id);
            const hasDetails = d.description || d.questions?.length || d.reference;
            
            return (
            <div
              key={d.id}
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
                onClick={() => hasDetails && setExpandedDocIds(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(d.id)) {
                    newSet.delete(d.id);
                  } else {
                    newSet.add(d.id);
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
                      {d.name}
                    </p>
                <p className={`text-xs mt-0.5 ${
                  darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
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
            <div className={`flex flex-wrap gap-3 text-xs ${
              darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
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
              </div>

            {/* EXPANDED DETAILS */}
            {isExpanded && hasDetails && (
              <div className={`px-4 pb-3 border-t border-[#0E1B2E]/10 ${
                darkMode ? "bg-gray-800/30" : "bg-white/20"
              }`}>
                <div className="space-y-3 pt-3">
                  {/* DESCRIPTION */}
                  {d.description && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <FileText className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          Description
                        </h4>
                      </div>
                      <div className={`text-xs ml-5 whitespace-pre-wrap ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                        {d.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
                      </div>
                    </div>
                  )}

                  {/* QUESTIONS */}
                  {d.questions && d.questions.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <HelpCircle className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          Questions ({d.questions.length})
                        </h4>
                      </div>
                      <ul className="ml-5 space-y-1.5">
                        {d.questions.map((q, idx) => (
                          <li key={idx} className={`text-xs flex items-start gap-2 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                            <span className="mt-0.5">{idx + 1}.</span>
                            <span>{q}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* REFERENCE */}
                  {d.reference && (
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <ExternalLink className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"}`} />
                        <h4 className={`text-xs font-medium ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                          References
                        </h4>
                      </div>
                      <div className={`text-xs ml-5 ${darkMode ? "text-gray-400" : "text-[#0E1B2E]/70"}`}>
                        {d.reference.split(', ').map((ref, idx) => (
                          <div key={idx} className="font-mono">{ref}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ================= ACTION ROW ================= */}
            <div className={`pt-3 border-t rounded-b-xl -mx-4 px-4 pb-1 transition-colors duration-300 border-[#0E1B2E]/10 ${
              darkMode
                ? "border-gray-700 bg-gray-900/50"
                : "bg-[#0E1B2E]/5"
            }`}>
              <div className="flex flex-wrap items-center gap-2">

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
                    px-2.5 py-1 rounded-lg text-xs font-medium border shadow-sm
                    focus:outline-none focus:ring-1 focus:ring-offset-0
                    ${getStatusStyles(d.status, darkMode)}
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
                    px-2.5 py-1 rounded-lg text-xs font-medium border shadow-sm
                    focus:outline-none focus:ring-1
                    ${darkMode
                      ? "border-gray-600 bg-gray-700/50 text-gray-100 focus:ring-[#0E1B2E]/20"
                      : "border-[#0E1B2E]/20 bg-white/60 text-[#0E1B2E] focus:ring-[#0E1B2E]/10"
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
                    px-3 py-1.5
                    rounded-lg
                    text-xs font-medium
                    shadow-sm hover:shadow-md
                    transition
                    ${
                      d.status === 'Complete'
                        ? darkMode
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : 'bg-[#0E1B2E]/20 text-[#0E1B2E]/40 cursor-not-allowed'
                        : darkMode
                          ? 'bg-[#0E1B2E] hover:bg-[#1a2f4d] text-white'
                          : 'bg-[#0E1B2E] hover:bg-[#1a2f4d] text-white'
                    }
                  `}
                >
                  Ask AI to Collect Info
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
            {docs.length === 0 
              ? 'No documentation items for this employee.'
              : 'No documents match the current filters.'}
          </div>
        )}
      </div>
    </div>
  );
}
