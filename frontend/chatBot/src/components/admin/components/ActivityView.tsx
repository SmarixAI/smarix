"use client";

import { Activity, Loader2 } from "lucide-react";

interface ActivityViewProps {
  darkMode: boolean;
  isRunning: boolean;
  organization: string;
  repoName: string;
}

export default function ActivityView({
  darkMode,
  isRunning,
  organization,
  repoName,
}: ActivityViewProps) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className={`rounded-xl shadow-lg p-6 ${
        darkMode ? "bg-gray-800" : "bg-white"
      }`}>
        <h2 className={`text-2xl font-semibold mb-6 ${
          darkMode ? "text-white" : "text-slate-900"
        }`}>
          Recent Activity
        </h2>
        <div className={`space-y-4 ${
          darkMode ? "text-gray-300" : "text-slate-600"
        }`}>
          {isRunning ? (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              <div>
                <p className="font-medium">Setup in progress...</p>
                <p className="text-sm opacity-75">
                  Processing {organization}/{repoName}
                </p>
              </div>
            </div>
          ) : (
            <div className={`text-center py-12 ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}>
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No active operations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

