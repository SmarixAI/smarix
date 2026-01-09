'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { BookOpen, Code, Wrench, Check, LogOut } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';
import Image from 'next/image';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

export default function Header({ activeTab, setActiveTab }: HeaderProps) {
  const router = useRouter();
  const { user, logout } = useAuth();

  const tabs = [
    { id: 'reading', label: 'Reading & Overview', shortLabel: 'Overview', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'practice', label: 'Practice Tasks', shortLabel: 'Practice', icon: <Code className="w-4 h-4" /> },
    { id: 'bugfix', label: 'Bug Fixing', shortLabel: 'Bug Fix', icon: <Wrench className="w-4 h-4" /> },
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
      <div className="max-w-[1800px] mx-auto px-6">
        {/* ===================== TOP ROW ===================== */}
        <div className="py-4 flex items-center justify-between">
          {/* LEFT — LOGO */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
              <Image
                src="/logo.png"
                alt="Smarix Logo"
                width={24}
                height={24}
                className="w-6 h-6 object-contain"
              />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-[#0E1B2E]">
                Smarix
              </h1>
              <p className="text-xs text-[#0E1B2E]/60">
                Onboarding Dashboard
              </p>
            </div>
          </div>

          {/* CENTER — TABS NAVIGATION */}
          <div className="flex items-center gap-1 absolute left-1/2 -translate-x-1/2">
            {tabs.map((tab, i) => {
              const status = getStepStatus(tab.id);
              const active = activeTab === tab.id;
              const done = status === 'completed';

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="relative flex items-center gap-2 px-4 py-2 rounded-lg transition-all group"
                >
                  {/* Progress indicator line */}
                  {i > 0 && (
                    <div className="absolute left-0 top-1/2 -translate-x-1/2 w-8 h-0.5 -translate-y-1/2">
                      <div className={`h-full transition-all duration-300 ${
                        done || active
                          ? 'bg-[#0E1B2E]'
                          : 'bg-[#0E1B2E]/20'
                      }`} />
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                        active
                          ? 'bg-[#0E1B2E] text-white'
                          : done
                          ? 'bg-[#0E1B2E]/10 text-[#0E1B2E]'
                          : 'bg-white border border-gray-200 text-[#0E1B2E]/40 group-hover:bg-[#0E1B2E]/5 group-hover:text-[#0E1B2E]/60'
                      }`}
                    >
                      {done ? (
                        <Check className="w-4 h-4 text-[#0E1B2E]" />
                      ) : (
                        <div className={`${active ? 'text-white' : ''}`}>
                          {tab.icon}
                        </div>
                      )}
                    </div>
                    <span
                      className={`text-sm font-medium transition-colors ${
                        active
                          ? 'text-[#0E1B2E]'
                          : done
                          ? 'text-[#0E1B2E]/80'
                          : 'text-[#0E1B2E]/60 group-hover:text-[#0E1B2E]/80'
                      }`}
                    >
                      {tab.shortLabel}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* RIGHT — PROFILE */}
          {user && (
            <div className="flex items-center gap-3 flex-shrink-0 ml-auto">
              <div className="text-right">
                <div className="text-sm font-semibold text-[#0E1B2E] truncate">
                  {user.name || user.username}
                </div>
                <div className="text-xs text-[#0E1B2E]/60 capitalize truncate">
                  {user.role || 'Employee'}
                </div>
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg hover:bg-red-50 transition-colors text-red-600"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Progress Indicator Bar */}
        <div className="relative h-1 bg-[#0E1B2E]/5 rounded-full mb-4">
          <div
            className="absolute top-0 left-0 h-full bg-[#0E1B2E] rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${((tabs.findIndex((t) => t.id === activeTab) + 1) / tabs.length) * 100}%`,
            }}
          />
        </div>
      </div>
    </header>
  );
}