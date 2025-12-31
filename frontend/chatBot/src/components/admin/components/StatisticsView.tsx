"use client";

import { Database, CheckCircle, AlertTriangle, Clock } from "lucide-react";
import { SetupStats } from "./types";

interface StatisticsViewProps {
  darkMode: boolean;
  stats: SetupStats;
}

export default function StatisticsView({
  darkMode,
  stats,
}: StatisticsViewProps) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className={`rounded-xl shadow-lg p-6 ${
        darkMode ? "bg-gray-800" : "bg-white"
      }`}>
        <h2 className={`text-2xl font-semibold mb-6 ${
          darkMode ? "text-white" : "text-slate-900"
        }`}>
          Statistics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`p-6 rounded-lg ${
            darkMode ? "bg-gray-700" : "bg-white"
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${
                darkMode ? "text-gray-300" : "text-slate-600"
              }`}>
                Total Setups
              </span>
              <Database className={`w-5 h-5 ${
                darkMode ? "text-blue-400" : "text-blue-600"
              }`} />
            </div>
            <p className={`text-3xl font-bold ${
              darkMode ? "text-white" : "text-slate-900"
            }`}>
              {stats.totalSetups}
            </p>
          </div>
          <div className={`p-6 rounded-lg ${
            darkMode ? "bg-gray-700" : "bg-white"
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${
                darkMode ? "text-gray-300" : "text-slate-600"
              }`}>
                Successful
              </span>
              <CheckCircle className={`w-5 h-5 ${
                darkMode ? "text-green-400" : "text-green-600"
              }`} />
            </div>
            <p className={`text-3xl font-bold ${
              darkMode ? "text-white" : "text-slate-900"
            }`}>
              {stats.successfulSetups}
            </p>
            {stats.totalSetups > 0 && (
              <p className={`text-xs mt-1 ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}>
                {((stats.successfulSetups / stats.totalSetups) * 100).toFixed(1)}% success rate
              </p>
            )}
          </div>
          <div className={`p-6 rounded-lg ${
            darkMode ? "bg-gray-700" : "bg-white"
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${
                darkMode ? "text-gray-300" : "text-slate-600"
              }`}>
                Failed
              </span>
              <AlertTriangle className={`w-5 h-5 ${
                darkMode ? "text-red-400" : "text-red-600"
              }`} />
            </div>
            <p className={`text-3xl font-bold ${
              darkMode ? "text-white" : "text-slate-900"
            }`}>
              {stats.failedSetups}
            </p>
          </div>
        </div>
        {stats.lastSetup && (
          <div className={`mt-6 p-4 rounded-lg ${
            darkMode ? "bg-gray-700" : "bg-slate-50"
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <Clock className={`w-4 h-4 ${
                darkMode ? "text-gray-400" : "text-gray-500"
              }`} />
              <span className={`text-sm font-medium ${
                darkMode ? "text-gray-300" : "text-slate-700"
              }`}>
                Last Setup
              </span>
            </div>
            <p className={`text-sm ${
              darkMode ? "text-gray-400" : "text-slate-600"
            }`}>
              {new Date(stats.lastSetup).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

