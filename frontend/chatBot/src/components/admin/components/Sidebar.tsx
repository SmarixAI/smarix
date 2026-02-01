"use client";

import { Database, History, UserPlus, UserMinus, Users, LogOut, Key } from "lucide-react";
import { Space_Grotesk, Fira_Code } from 'next/font/google';
import { useAuth } from "@/components/auth/AuthContext";
import Image from 'next/image';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const firaCode = Fira_Code({ subsets: ['latin'] });

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onOpenChangePassword: () => void;
}

export default function Sidebar({
  activeView,
  setActiveView,
  onOpenChangePassword,
}: SidebarProps) {
  const { user, logout } = useAuth();

  return (
    <aside className="w-80 flex-shrink-0 border-r border-gray-200 bg-white relative z-10 flex flex-col">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 bg-[#0E1B2E] rounded-xl flex items-center justify-center overflow-hidden">
            <Image
              src="/logo.png"
              alt="Smarix Logo"
              width={24}
              height={24}
              className="w-6 h-6 object-contain"
            />
          </div>
          <h2 className={`${spaceGrotesk.className} text-xl font-bold tracking-tight text-[#0E1B2E]`}>
            Smarix
          </h2>
        </div>
        <p className={`${firaCode.className} text-sm text-[#0E1B2E]/60 ml-11`}>
          Admin Panel
        </p>
      </div>

      {/* Profile & Logout */}
      <div className="p-4 border-b border-gray-200">
        {user && (
          <>
            <div className="flex items-center justify-between mb-3">
              <div className="flex-1 min-w-0">
                <div className={`${spaceGrotesk.className} text-sm font-semibold text-[#0E1B2E] truncate`}>
                  {user.name || user.username}
                </div>
                <div className={`${firaCode.className} text-xs text-[#0E1B2E]/60 capitalize truncate`}>
                  {user.role === 'admin' ? 'Administrator' : user.role}
                </div>
              </div>
              <div className="flex items-center gap-1 ml-2">
                <button
                  onClick={onOpenChangePassword}
                  className="p-2 rounded-lg hover:bg-[#0E1B2E]/5 transition-colors text-[#0E1B2E]/70 hover:text-[#0E1B2E]"
                  title="Change Password"
                >
                  <Key className="w-4 h-4" />
                </button>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg hover:bg-red-50 transition-colors text-red-600"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1.5">
        <button
          onClick={() => setActiveView("setup")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "setup"
              ? "bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/20"
              : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] hover:translate-x-1"
          }`}
        >
          <Database className={`w-5 h-5 ${activeView === "setup" ? "scale-110" : ""} transition-transform`} />
          <span className={`${spaceGrotesk.className} font-medium`}>Add New Repo</span>
        </button>
        <button
          onClick={() => setActiveView("history")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            activeView === "history"
              ? "bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/20"
              : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] hover:translate-x-1"
          }`}
        >
          <History className={`w-5 h-5 ${activeView === "history" ? "scale-110" : ""} transition-transform`} />
          <span className={`${spaceGrotesk.className} font-medium`}>History</span>
        </button>
        <div className="pt-4 mt-4 border-t border-gray-200/50">
          <button
            onClick={() => setActiveView("users")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "users"
                ? "bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/20"
                : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] hover:translate-x-1"
            }`}
          >
            <Users className={`w-5 h-5 ${activeView === "users" ? "scale-110" : ""} transition-transform`} />
            <span className={`${spaceGrotesk.className} font-medium`}>User Management</span>
          </button>
          <button
            onClick={() => setActiveView("onboarding")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "onboarding"
                ? "bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/20"
                : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] hover:translate-x-1"
            }`}
          >
            <UserPlus className={`w-5 h-5 ${activeView === "onboarding" ? "scale-110" : ""} transition-transform`} />
            <span className={`${spaceGrotesk.className} font-medium`}>Onboarding</span>
          </button>
          {/* <button
            onClick={() => setActiveView("offboarding")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeView === "offboarding"
                ? "bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/20"
                : "hover:bg-[#0E1B2E]/5 text-[#0E1B2E] hover:translate-x-1"
            }`}
          >
            <UserMinus className={`w-5 h-5 ${activeView === "offboarding" ? "scale-110" : ""} transition-transform`} />
            <span className={`${spaceGrotesk.className} font-medium`}>Offboarding</span>
          </button> */}
        </div>
      </nav>
    </aside>
  );
}

