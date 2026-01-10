"use client";

import { Moon, Sun, User, Settings, LogOut, ShieldCheck, Key } from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import ChangePasswordModal from "@/components/auth/ChangePasswordModal";
import { useState } from "react";
import { Space_Grotesk, Fira_Code } from 'next/font/google';
import Image from 'next/image';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const firaCode = Fira_Code({ subsets: ['latin'] });

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
    <nav className="sticky top-0 z-50 border-b border-gray-200/50 backdrop-blur-xl bg-white/80 transition-colors">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* LEFT */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#0E1B2E] flex items-center justify-center overflow-hidden">
              <Image src="/logo.png" alt="Logo" width={20} height={20} className="object-contain" />
            </div>
            <div>
              <h1 className={`${spaceGrotesk.className} text-lg font-semibold flex items-center gap-2 text-[#0E1B2E]`}>
                Admin Panel
              </h1>
              <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                Repository Pipeline Manager
              </p>
            </div>
          </div>

          {/* RIGHT */}
          <div className="flex items-center gap-3">
            {/* THEME TOGGLE */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg transition hover:bg-[#0E1B2E]/5 text-[#0E1B2E]/70 hover:text-[#0E1B2E]"
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
                className="p-2 rounded-full transition hover:bg-[#0E1B2E]/5 text-[#0E1B2E]/70"
              >
                <User className="w-5 h-5" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-50"
                    onClick={() => setUserMenuOpen(false)}
                  />

                  <div className="absolute right-0 mt-2 w-52 rounded-xl border border-gray-200/50 shadow-xl z-20 bg-white/90 backdrop-blur-xl">
                    <div className="px-4 py-3 border-b border-gray-200/50">
                      <p className={`${spaceGrotesk.className} text-sm font-medium text-[#0E1B2E]`}>
                        {user?.username || 'Admin User'}
                      </p>
                      <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                        {user?.role === 'admin' ? 'Administrator' : `Employee ID: ${user?.employeeId || 'N/A'}`}
                      </p>
                    </div>

                    <div className="p-2 space-y-1">
                      <button
                        onClick={() => {
                          setShowChangePassword(true);
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition hover:bg-[#0E1B2E]/5 text-[#0E1B2E]"
                      >
                        <Key className="w-4 h-4" />
                        Change Password
                      </button>
                      <button
                        onClick={logout}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition hover:bg-red-50 text-red-600"
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

