'use client';

import { useEffect, useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, FileText, HelpCircle, ExternalLink, Filter, AlertCircle, RefreshCw } from 'lucide-react';
import Loader from '../Loader';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

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
      ? 'bg-red-900/40 text-red-200 border-red-800'
      : status === 'Partial'
      ? 'bg-amber-900/40 text-amber-200 border-amber-800'
      : 'bg-emerald-900/40 text-emerald-200 border-emerald-800';
  }
  return status === 'Missing'
    ? 'bg-red-50 text-red-700 border-red-200'
    : status === 'Partial'
    ? 'bg-amber-50 text-amber-700 border-amber-200'
    : 'bg-emerald-50 text-emerald-700 border-emerald-200';
};

const getPriorityStyles = (priority: DocPriority, darkMode: boolean): string => {
  if (darkMode) {
    return priority === 'High'
      ? 'text-red-300'
      : priority === 'Medium'
      ? 'text-amber-300'
      : 'text-emerald-300';
  }
  return priority === 'High'
    ? 'text-red-700'
    : priority === 'Medium'
    ? 'text-amber-700'
    : 'text-emerald-700';
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

    if (!employeeId?.trim()) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        const response = await fetch(`/api/offboarding/documents?employeeId=${encodeURIComponent(employeeId)}`);
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

        // Set documents if employee found
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
    <div className={`space-y-4 p-1 ${inter.className}`}>

      {/* ================= FILTERS ================= */}
      <div className={`rounded-xl border px-4 py-3 flex items-center gap-4 transition-colors ${
        darkMode
          ? "border-gray-700 bg-gray-800/50"
          : "border-slate-200 bg-white shadow-sm"
      }`}>
        <div className="flex items-center gap-2">
          <Filter className={`w-4 h-4 ${darkMode ? "text-gray-400" : "text-slate-500"}`} />
          <span className={`text-sm font-semibold ${darkMode ? "text-gray-200" : "text-[#0E1B2E]"}`}>Filters</span>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <label className={`text-xs font-medium ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>Status:</label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as any)}
              className={`
                px-2.5 py-1.5 rounded-lg text-xs font-medium border outline-none focus:ring-2
                transition-all cursor-pointer
                ${darkMode
                  ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                  : "border-slate-200 bg-slate-50 text-slate-700 focus:ring-blue-500/20 hover:border-slate-300"
                }
              `}
            >
              <option value="All">All</option>
              <option value="Missing">Missing</option>
              <option value="Partial">Partial</option>
              <option value="Complete">Complete</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="flex items-center gap-2">
            <label className={`text-xs font-medium ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value as any)}
              className={`
                px-2.5 py-1.5 rounded-lg text-xs font-medium border outline-none focus:ring-2
                transition-all cursor-pointer
                ${darkMode
                  ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                  : "border-slate-200 bg-slate-50 text-slate-700 focus:ring-blue-500/20 hover:border-slate-300"
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
      <h2 className={`text-xs font-bold uppercase tracking-wider mb-2 px-1 ${
        darkMode ? "text-gray-400" : "text-[#0E1B2E]/60"
      }`}>
        Mandatory Documents ({filteredDocs.length})
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
              className={`rounded-xl border overflow-hidden transition-all duration-300 ${
                darkMode
                  ? "border-gray-700 bg-gray-800/30"
                  : "border-slate-200 bg-white shadow-sm hover:shadow-md"
              }`}
            >
              {/* TOP ROW */}
              <div 
                className={`flex items-start justify-between gap-4 p-4 cursor-pointer transition-colors ${
                  hasDetails ? (darkMode ? "hover:bg-gray-800/70" : "hover:bg-slate-50") : ""
                } ${isExpanded ? (darkMode ? "bg-gray-800/30" : "bg-slate-50/50") : ""}`}
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
                <div className="flex-1 flex items-start gap-3">
                  {hasDetails && (
                    <div className="mt-0.5 text-slate-400">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                  )}
                  <div>
                    <p className={`text-sm font-semibold ${
                      darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                    }`}>
                      {d.name}
                    </p>
                    <div className={`text-xs mt-1 flex items-center gap-2 ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      <span>Owner:</span>
                      <span className={`font-medium px-1.5 py-0.5 rounded ${
                        darkMode ? "bg-gray-700 text-gray-200" : "bg-slate-100 text-slate-700"
                      }`}>
                        {d.owner}
                      </span>
                    </div>
                  </div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border ${getStatusStyles(d.status, darkMode)}`}
                >
                  {d.status}
                </span>
              </div>

              {/* META INFO */}
              <div className={`px-4 pb-3 flex flex-wrap gap-4 text-xs ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-400">Priority:</span>
                  <span className={`font-bold ${getPriorityStyles(d.priority, darkMode)}`}>
                    {d.priority}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <RefreshCw className="w-3 h-3" />
                  <span>Updated {d.lastUpdated}</span>
                </div>

                {d.aiFollowUp && (
                  <div className={`flex items-center gap-1 font-semibold ${
                    darkMode ? "text-indigo-400" : "text-indigo-600"
                  }`}>
                    <span className="text-lg leading-none">🤖</span>
                    AI Follow-up
                  </div>
                )}
              </div>

              {/* EXPANDED DETAILS */}
              {isExpanded && hasDetails && (
                <div className={`px-4 py-3 border-t border-dashed border-[#0E1B2E]/10 ${
                  darkMode ? "bg-gray-800/20" : "bg-slate-50/50"
                }`}>
                  <div className="space-y-4 pl-7">
                    {/* DESCRIPTION */}
                    {d.description && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-slate-500"}`} />
                          <h4 className={`text-xs font-bold uppercase tracking-wider ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                            Description
                          </h4>
                        </div>
                        <div className={`text-xs whitespace-pre-wrap leading-relaxed ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                          {d.description.replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '')}
                        </div>
                      </div>
                    )}

                    {/* QUESTIONS */}
                    {d.questions && d.questions.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <HelpCircle className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-slate-500"}`} />
                          <h4 className={`text-xs font-bold uppercase tracking-wider ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                            Required Information
                          </h4>
                        </div>
                        <ul className="space-y-1">
                          {d.questions.map((q, idx) => (
                            <li key={idx} className={`text-xs flex items-start gap-2 ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                              <span className="mt-0.5">•</span>
                              <span>{q}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* REFERENCE */}
                    {d.reference && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <ExternalLink className={`w-3.5 h-3.5 ${darkMode ? "text-gray-400" : "text-slate-500"}`} />
                          <h4 className={`text-xs font-bold uppercase tracking-wider ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                            References
                          </h4>
                        </div>
                        <div className={`text-xs ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                          {d.reference.split(', ').map((ref, idx) => (
                            <div key={idx} className="font-mono bg-slate-100 dark:bg-gray-800 px-2 py-1 rounded w-fit mb-1">{ref}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ================= ACTION ROW ================= */}
              <div className={`p-3 border-t bg-slate-50/50 ${
                darkMode ? "border-gray-700 bg-gray-800/30" : "border-slate-100"
              }`}>
                <div className="flex flex-wrap items-center gap-3">

                  {/* Status Select */}
                  <div className="relative">
                    <select
                      key={`${d.id}-status-${d.status}-${updateCounter}`}
                      value={d.status}
                      onChange={e =>
                        updateDoc(d.id, {
                          status: e.target.value as DocStatus
                        })
                      }
                      className={`
                        appearance-none pl-3 pr-8 py-1.5 rounded-lg text-xs font-bold border cursor-pointer outline-none focus:ring-2
                        transition-all duration-200
                        ${getStatusStyles(d.status, darkMode)}
                      `}
                    >
                      <option value="Missing">Missing</option>
                      <option value="Partial">Partial</option>
                      <option value="Complete">Complete</option>
                    </select>
                    <ChevronDown className={`w-3 h-3 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none opacity-50 ${
                       d.status === 'Missing' ? (darkMode ? "text-red-200" : "text-red-700") :
                       d.status === 'Partial' ? (darkMode ? "text-amber-200" : "text-amber-800") :
                       (darkMode ? "text-emerald-200" : "text-emerald-700")
                    }`} />
                  </div>

                  <div className="h-4 w-px bg-slate-200 dark:bg-gray-700"></div>

                  {/* Priority Select */}
                  <div className="relative">
                    <select
                      key={`${d.id}-priority-${d.priority}-${updateCounter}`}
                      value={d.priority}
                      onChange={e =>
                        updateDoc(d.id, {
                          priority: e.target.value as DocPriority
                        })
                      }
                      className={`
                        appearance-none pl-3 pr-8 py-1.5 rounded-lg text-xs font-medium border cursor-pointer outline-none focus:ring-2
                        transition-all duration-200
                        ${darkMode
                          ? "border-gray-600 bg-gray-700 text-white focus:ring-blue-500/50"
                          : "border-slate-200 bg-white text-slate-700 focus:ring-blue-500/20 hover:border-slate-300"
                        }
                      `}
                    >
                      <option value="High">High Priority</option>
                      <option value="Medium">Medium Priority</option>
                      <option value="Low">Low Priority</option>
                    </select>
                    <ChevronDown className={`w-3 h-3 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none opacity-50 ${darkMode ? "text-gray-400" : "text-slate-500"}`} />
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={() => askAI(d)}
                    disabled={d.status === 'Complete'}
                    className={`
                      ml-auto px-4 py-1.5 rounded-lg text-xs font-bold shadow-sm transition-all
                      ${
                        d.status === 'Complete'
                          ? darkMode
                            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                          : darkMode
                            ? 'bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-900/20'
                            : 'bg-[#0E1B2E] hover:bg-blue-900 text-white hover:shadow-lg hover:scale-105'
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
          <div className="p-8 text-center flex flex-col items-center justify-center gap-2 opacity-60">
            <div className={`p-3 rounded-full ${darkMode ? "bg-gray-800" : "bg-slate-50"}`}>
              <AlertCircle className="w-6 h-6 text-slate-400" />
            </div>
            <p className={`text-sm ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
              {docs.length === 0 
                ? 'No documentation items for this employee.'
                : 'No documents match the current filters.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}