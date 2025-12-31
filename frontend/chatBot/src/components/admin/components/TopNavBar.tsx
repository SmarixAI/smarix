"use client";

import { Moon, Sun, User, Settings, LogOut, ShieldCheck, Key } from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import ChangePasswordModal from "@/components/auth/ChangePasswordModal";
import { useState } from "react";

interface TopNavBarProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  userMenuOpen: boolean;
  setUserMenuOpen: (value: boolean) => void;
}

export default function TopNavBar({
  darkMode,
  setDarkMode,
  userMenuOpen,
  setUserMenuOpen,
}: TopNavBarProps) {
  const { user, logout } = useAuth();
  const [showChangePassword, setShowChangePassword] = useState(false);

  return (
    <nav
      className={`sticky top-0 z-50 border-b backdrop-blur-md transition-colors ${
        darkMode
          ? "bg-gray-900/90 border-gray-700"
          : "bg-white/90 border-slate-200"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* LEFT */}
          <div>
            <h1
              className={`text-lg font-semibold flex items-center gap-2 ${
                darkMode ? "text-white" : "text-slate-900"
              }`}
            >
              <ShieldCheck className="w-5 h-5" />
              Admin Panel
            </h1>
            <p
              className={`text-xs ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}
            >
              Repository Pipeline Manager
            </p>
          </div>

          {/* RIGHT */}
          <div className="flex items-center gap-3">
            {/* THEME TOGGLE */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg transition ${
                darkMode
                  ? "hover:bg-gray-800 text-yellow-400"
                  : "hover:bg-blue-50 text-blue-600"
              }`}
              title={darkMode ? "Light mode" : "Dark mode"}
            >
              {darkMode ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>

            {/* USER MENU */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className={`p-2 rounded-full transition ${
                  darkMode
                    ? "hover:bg-gray-800 text-gray-300"
                    : "hover:bg-blue-50 text-slate-700"
                }`}
              >
                <User className="w-5 h-5" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-50"
                    onClick={() => setUserMenuOpen(false)}
                  />

                  <div
                    className={`absolute right-0 mt-2 w-52 rounded-xl border shadow-xl z-20 ${
                      darkMode
                        ? "bg-gray-900 border-gray-700"
                        : "bg-white border-slate-200"
                    }`}
                  >
                    <div className="px-4 py-3 border-b dark:border-gray-700">
                      <p
                        className={`text-sm font-medium ${
                          darkMode ? "text-white" : "text-slate-900"
                        }`}
                      >
                        {user?.username || 'Admin User'}
                      </p>
                      <p
                        className={`text-xs ${
                          darkMode ? "text-gray-400" : "text-slate-500"
                        }`}
                      >
                        {user?.role === 'admin' ? 'Administrator' : `Employee ID: ${user?.employeeId || 'N/A'}`}
                      </p>
                    </div>

                    <div className="p-2 space-y-1">
                      <button
                        onClick={() => {
                          setShowChangePassword(true);
                          setUserMenuOpen(false);
                        }}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                          darkMode
                            ? "hover:bg-gray-800 text-gray-300"
                            : "hover:bg-blue-50 text-slate-700"
                        }`}
                      >
                        <Key className="w-4 h-4" />
                        Change Password
                      </button>
                      <button
                        onClick={logout}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                          darkMode
                            ? "hover:bg-gray-800 text-gray-300"
                            : "hover:bg-blue-50 text-slate-700"
                        }`}
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={showChangePassword}
        onClose={() => setShowChangePassword(false)}
        darkMode={darkMode}
      />
    </nav>
  );
}

