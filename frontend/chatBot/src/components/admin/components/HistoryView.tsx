"use client";

import { History, CheckCircle, AlertTriangle, BookOpen, Bug, GraduationCap, MessageSquare, Settings } from "lucide-react";
import { HistoryEntry } from "./types";

interface HistoryViewProps {
  darkMode: boolean;
  setupHistory: HistoryEntry[];
}

const categoryIcons: { [key: string]: any } = {
  reading: BookOpen,
  bugfix: Bug,
  practice: GraduationCap,
  qna: MessageSquare,
};

const categoryNames: { [key: string]: string } = {
  reading: "Reading",
  bugfix: "BugFix",
  practice: "Practice",
  qna: "QnA",
};

export default function HistoryView({
  darkMode,
  setupHistory,
}: HistoryViewProps) {
  const getActionTitle = (entry: HistoryEntry) => {
    if (entry.action_type === "onboarding") {
      return "Onboarding Generation";
    } else if (entry.organization && entry.repo) {
      return `${entry.organization}/${entry.repo}`;
    }
    // Backward compatibility: if no action_type but has org/repo, it's a setup
    return entry.organization && entry.repo ? `${entry.organization}/${entry.repo}` : "Setup";
  };

  const getActionIcon = (entry: HistoryEntry) => {
    if (entry.action_type === "onboarding") {
      return BookOpen;
    } else if (entry.action_type === "offboarding") {
      return Settings;
    }
    return null;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className={`rounded-xl shadow-lg p-6 ${
        darkMode ? "bg-gray-800" : "bg-white"
      }`}>
        <h2 className={`text-2xl font-semibold mb-6 ${
          darkMode ? "text-white" : "text-slate-900"
        }`}>
          Action History
        </h2>
        {setupHistory.length === 0 ? (
          <div className={`text-center py-12 ${
            darkMode ? "text-gray-400" : "text-slate-500"
          }`}>
            <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No setup history yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {setupHistory.map((entry) => (
              <div
                key={entry.id}
                className={`p-4 rounded-lg border ${
                  entry.status === "success"
                    ? darkMode
                      ? "bg-green-900/20 border-green-700"
                      : "bg-green-50 border-green-200"
                    : darkMode
                    ? "bg-red-900/20 border-red-700"
                    : "bg-red-50 border-red-200"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1">
                    {entry.status === "success" ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                    {getActionIcon(entry) && (
                      (() => {
                        const Icon = getActionIcon(entry);
                        return <Icon className={`w-4 h-4 ${
                          entry.action_type === "onboarding"
                            ? darkMode ? "text-blue-400" : "text-blue-600"
                            : darkMode ? "text-purple-400" : "text-purple-600"
                        }`} />;
                      })()
                    )}
                    <div className="flex flex-col flex-1">
                      <span className={`font-semibold ${
                        darkMode ? "text-white" : "text-slate-900"
                      }`}>
                        {getActionTitle(entry)}
                      </span>
                      {/* Setup entries */}
                      {entry.organization && entry.repo && (
                        <>
                          {entry.execution_mode === "step-by-step" && entry.step_name && (
                            <span className={`text-xs mt-0.5 ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}>
                              Step: {entry.step_name}
                            </span>
                          )}
                          {entry.execution_mode === "full" && (
                            <span className={`text-xs mt-0.5 ${
                              darkMode ? "text-blue-400" : "text-blue-600"
                            }`}>
                              Full Pipeline
                            </span>
                          )}
                        </>
                      )}
                      {/* Onboarding entries */}
                      {entry.action_type === "onboarding" && (
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          {entry.categories && entry.categories.length > 0 && (
                            <div className="flex items-center gap-1 flex-wrap">
                              <span className={`text-xs ${
                                darkMode ? "text-gray-400" : "text-slate-500"
                              }`}>
                                Categories:
                              </span>
                              {entry.categories.map((cat) => {
                                const Icon = categoryIcons[cat];
                                const name = categoryNames[cat] || cat;
                                return (
                                  <span
                                    key={cat}
                                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                                      darkMode
                                        ? "bg-gray-700 text-gray-300"
                                        : "bg-slate-200 text-slate-700"
                                    }`}
                                  >
                                    {Icon && <Icon className="w-3 h-3" />}
                                    {name}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                          {entry.generator_count && (
                            <span className={`text-xs ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}>
                              ({entry.generator_count} generator{entry.generator_count !== 1 ? 's' : ''})
                            </span>
                          )}
                        </div>
                      )}
                      {/* Offboarding entries */}
                      {entry.action_type === "offboarding" && (
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          <span className={`text-xs ${
                            darkMode ? "text-purple-400" : "text-purple-600"
                          }`}>
                            Offboarding Data Generation
                          </span>
                          {entry.step_count && (
                            <span className={`text-xs ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}>
                              ({entry.step_count} step{entry.step_count !== 1 ? 's' : ''})
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <span className={`text-xs whitespace-nowrap ml-2 ${
                    darkMode ? "text-gray-400" : "text-slate-500"
                  }`}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>
                {entry.error && (
                  <p className={`text-sm mt-2 ${
                    darkMode ? "text-red-400" : "text-red-600"
                  }`}>
                    Error: {entry.error}
                  </p>
                )}
                {entry.duration && (
                  <p className={`text-xs mt-1 ${
                    darkMode ? "text-gray-400" : "text-slate-500"
                  }`}>
                    Duration: {(entry.duration / 1000).toFixed(1)}s
                  </p>
                )}
                {/* Show selected generators for onboarding if available */}
                {entry.action_type === "onboarding" && entry.selected_generators && entry.selected_generators.length > 0 && (
                  <details className={`mt-2 ${
                    darkMode ? "text-gray-300" : "text-slate-700"
                  }`}>
                    <summary className={`text-xs cursor-pointer hover:underline ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      View {entry.selected_generators.length} selected generator{entry.selected_generators.length !== 1 ? 's' : ''}
                    </summary>
                    <div className={`mt-2 p-2 rounded text-xs ${
                      darkMode ? "bg-gray-700/50" : "bg-slate-100"
                    }`}>
                      <div className="flex flex-wrap gap-1">
                        {entry.selected_generators.map((gen) => (
                          <span
                            key={gen}
                            className={`px-1.5 py-0.5 rounded ${
                              darkMode
                                ? "bg-gray-600 text-gray-300"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {gen.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  </details>
                )}
                {/* Show selected steps for offboarding if available */}
                {entry.action_type === "offboarding" && entry.selected_steps && entry.selected_steps.length > 0 && (
                  <details className={`mt-2 ${
                    darkMode ? "text-gray-300" : "text-slate-700"
                  }`}>
                    <summary className={`text-xs cursor-pointer hover:underline ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      View {entry.selected_steps.length} selected step{entry.selected_steps.length !== 1 ? 's' : ''}
                    </summary>
                    <div className={`mt-2 p-2 rounded text-xs ${
                      darkMode ? "bg-gray-700/50" : "bg-slate-100"
                    }`}>
                      <div className="flex flex-wrap gap-1">
                        {entry.selected_steps.map((step) => (
                          <span
                            key={step}
                            className={`px-1.5 py-0.5 rounded ${
                              darkMode
                                ? "bg-gray-600 text-gray-300"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {step.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

