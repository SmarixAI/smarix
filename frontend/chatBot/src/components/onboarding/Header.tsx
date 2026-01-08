'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { BookOpen, Code, Wrench, Check, User, LogOut } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

export default function Header({ activeTab, setActiveTab }: HeaderProps) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    setUserMenuOpen(false);
    // Use the AuthContext logout function which properly handles token clearing and logout flag
    logout();
  };

  const tabs = [
    { id: 'reading', label: 'Reading & Overview', shortLabel: 'Reading & Overview', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'practice', label: 'Practice Tasks', shortLabel: 'Practice Tasks', icon: <Code className="w-4 h-4" /> },
    { id: 'bugfix', label: 'Bug Fixing', shortLabel: 'Bug Fixing', icon: <Wrench className="w-4 h-4" /> },
  ];

  const getStepStatus = (tabId: string) => {
    const index = tabs.findIndex((t) => t.id === tabId);
    const activeIndex = tabs.findIndex((t) => t.id === activeTab);
    if (index < activeIndex) return 'completed';
    if (index === activeIndex) return 'current';
    return 'available';
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      {/* ===================== TOP ROW ===================== */}
      <div className="max-w-[1800px] mx-auto px-6 py-3 flex items-center justify-between">

        {/* LEFT — LOGO + TITLE */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-white border border-gray-200">
            <BookOpen className="w-6 h-6 text-gray-700" />
          </div>

          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              Onboarding Hub
            </h1>

            <p className="text-xs text-gray-600">
              Your personalized learning roadmap
            </p>
          </div>
        </div>

        {/* RIGHT — USER */}
        <div className="flex items-center space-x-4 flex-shrink-0">
          {/* USER MENU */}
          {user && (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="p-2 rounded-full transition hover:bg-gray-100 text-gray-700"
              >
                <User className="w-5 h-5" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setUserMenuOpen(false)}
                  />

                  <div className="absolute right-0 mt-2 w-52 rounded-lg border border-gray-200 shadow-lg bg-white z-20">
                    <div className="px-4 py-3 border-b border-gray-200">
                      <p className="text-sm font-medium text-gray-900">
                        {user.name || user.username}
                      </p>
                      <p className="text-xs text-gray-500">
                        Employee
                      </p>
                    </div>

                    <div className="p-2 space-y-1">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition hover:bg-gray-100 text-gray-700"
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ===================== PROGRESS BAR SECTION ===================== */}
      <div className="max-w-[1800px] mx-auto px-6 pb-4 bg-gray-50">
        <div className="relative">

          {/* Background bar */}
          <div
            className="absolute top-4 left-0 right-0 h-1 bg-gray-200 rounded-full"
            style={{ marginLeft: '2rem', marginRight: '2rem' }}
          />

          {/* Smooth progress line */}
          <div
            className="absolute top-4 left-0 h-1 rounded-full transition-all duration-500 ease-out bg-gray-400"
            style={{
              width: `${((tabs.findIndex((t) => t.id === activeTab)) / (tabs.length - 1)) * 100}%`,
              marginLeft: '2rem',
              marginRight: '2rem'
            }}
          />

          {/* Step indicators */}
          <div className="relative flex justify-between items-start mt-8">
            {tabs.map((tab, i) => {
              const status = getStepStatus(tab.id);
              const active = activeTab === tab.id;
              const done = status === 'completed';

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="flex flex-col items-center space-y-2 cursor-pointer transition-all"
                  style={{ flex: 1 }}
                >
                  <div className="relative">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
                        active
                          ? 'bg-gray-800 text-white ring-2 ring-gray-400'
                          : done
                          ? 'bg-gray-200 text-gray-600'
                          : 'bg-gray-100 border border-gray-300 text-gray-500'
                      }`}
                    >
                      {done ? <Check className="w-5 h-5 text-gray-700" /> : tab.icon}
                    </div>
                  </div>

                  <p
                    className={`text-xs font-medium leading-tight ${
                      active
                        ? 'text-gray-900'
                        : 'text-gray-600'
                    }`}
                  >
                    {tab.shortLabel}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
}