"use client";

import { Database, History, BarChart3, Activity, UserPlus, UserMinus, Users } from "lucide-react";
import { SetupStats } from "./types";

interface SidebarProps {
  darkMode: boolean;
  activeView: string;
  setActiveView: (view: string) => void;
  stats: SetupStats;
}

export default function Sidebar({
  darkMode,
  activeView,
  setActiveView,
  stats,
}: SidebarProps) {
  return (
    <aside className={`w-64 border-r min-h-[calc(100vh-4rem)] p-4 transition-all duration-300 ${
      darkMode 
        ? "bg-gray-800/95 border-gray-700 backdrop-blur-sm" 
        : "bg-white/95 border-slate-200 backdrop-blur-sm"
    }`}>
      <nav className="space-y-1.5">
        <button
          onClick={() => setActiveView("setup")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "setup"
              ? darkMode
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
              : darkMode
              ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
              : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
          }`}
        >
          <Database className={`w-5 h-5 ${activeView === "setup" ? "scale-110" : ""} transition-transform`} />
          <span className="font-medium">Setup Pipeline</span>
        </button>
        <button
          onClick={() => setActiveView("history")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "history"
              ? darkMode
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
              : darkMode
              ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
              : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
          }`}
        >
          <History className={`w-5 h-5 ${activeView === "history" ? "scale-110" : ""} transition-transform`} />
          <span className="font-medium">History</span>
        </button>
        <button
          onClick={() => setActiveView("stats")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "stats"
              ? darkMode
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
              : darkMode
              ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
              : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
          }`}
        >
          <BarChart3 className={`w-5 h-5 ${activeView === "stats" ? "scale-110" : ""} transition-transform`} />
          <span className="font-medium">Statistics</span>
        </button>
        <button
          onClick={() => setActiveView("activity")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "activity"
              ? darkMode
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
              : darkMode
              ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
              : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
          }`}
        >
          <Activity className={`w-5 h-5 ${activeView === "activity" ? "scale-110" : ""} transition-transform`} />
          <span className="font-medium">Activity</span>
        </button>
        <div className="pt-2 mt-2 border-t border-slate-200 dark:border-gray-700">
          <button
            onClick={() => setActiveView("users")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "users"
                ? darkMode
                  ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/20"
                  : "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30"
                : darkMode
                ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
                : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
            }`}
          >
            <Users className={`w-5 h-5 ${activeView === "users" ? "scale-110" : ""} transition-transform`} />
            <span className="font-medium">User Management</span>
          </button>
          <button
            onClick={() => setActiveView("onboarding")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "onboarding"
                ? darkMode
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/20"
                  : "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/30"
                : darkMode
                ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
                : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
            }`}
          >
            <UserPlus className={`w-5 h-5 ${activeView === "onboarding" ? "scale-110" : ""} transition-transform`} />
            <span className="font-medium">Onboarding</span>
          </button>
          <button
            onClick={() => setActiveView("offboarding")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "offboarding"
                ? darkMode
                  ? "bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-lg shadow-rose-500/20"
                  : "bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-lg shadow-rose-500/30"
                : darkMode
                ? "hover:bg-gray-700/50 text-gray-300 hover:translate-x-1"
                : "hover:bg-slate-100 text-slate-700 hover:translate-x-1"
            }`}
          >
            <UserMinus className={`w-5 h-5 ${activeView === "offboarding" ? "scale-110" : ""} transition-transform`} />
            <span className="font-medium">Offboarding</span>
          </button>
        </div>
      </nav>

      {/* Stats Card in Sidebar */}
      <div className={`mt-6 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 ${
        darkMode 
          ? "bg-gray-700/50 border-gray-600 shadow-lg" 
          : "bg-gradient-to-br from-slate-50 to-white border-slate-200 shadow-md"
      }`}>
        <h3 className={`text-sm font-semibold mb-3 ${
          darkMode ? "text-gray-300" : "text-slate-700"
        }`}>
          Quick Stats
        </h3>
        <div className="space-y-2.5">
          <div className="flex justify-between items-center text-xs">
            <span className={darkMode ? "text-gray-400" : "text-slate-600"}>
              Total Setups
            </span>
            <span className={`font-bold text-sm ${
              darkMode ? "text-white" : "text-slate-900"
            }`}>
              {stats.totalSetups}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className={darkMode ? "text-gray-400" : "text-slate-600"}>
              Successful
            </span>
            <span className="font-bold text-sm text-emerald-600 dark:text-emerald-400">
              {stats.successfulSetups}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className={darkMode ? "text-gray-400" : "text-slate-600"}>
              Failed
            </span>
            <span className="font-bold text-sm text-rose-600 dark:text-rose-400">
              {stats.failedSetups}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

