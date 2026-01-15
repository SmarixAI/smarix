'use client';

import { useState, useEffect } from 'react';
import { BookOpen, Code, Wrench, Check, ArrowLeft } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';
import Image from 'next/image';
import { Inter } from 'next/font/google';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

export default function Header({ activeTab, setActiveTab }: HeaderProps) {
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
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 shadow-sm">
      <div className="max-w-[1800px] mx-auto px-6">
        <div className="py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-10 h-10 bg-gradient-to-br from-[#0E1B2E] to-blue-900 rounded-xl flex items-center justify-center overflow-hidden shadow-md shadow-slate-300/30 border border-slate-200/40">
              <Image
                src="/logo.png"
                alt="Smarix Logo"
                width={28}
                height={28}
                className="w-7 h-7 object-contain"
              />
            </div>
            <div>
              <h1 className={`${inter.className} text-xl font-bold tracking-tight text-[#0E1B2E]`}>
                Smarix
              </h1>
              <p className={`${inter.className} text-xs text-slate-600 font-medium`}>
                Onboarding Dashboard
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 absolute left-1/2 -translate-x-1/2">
            {tabs.map((tab, i) => {
              const status = getStepStatus(tab.id);
              const active = activeTab === tab.id;
              const done = status === 'completed';

              return (
                <div key={tab.id} className="flex items-center">
                  {i > 0 && (
                    <div className="w-8 h-0.5 mx-1">
                      <div className={`h-full transition-all duration-300 rounded-full ${
                        done || active
                          ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-600'
                          : 'bg-slate-200'
                      }`} />
                    </div>
                  )}

                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={`${inter.className} relative flex items-center gap-2.5 px-4 py-2.5 rounded-xl transition-all group ${
                      active
                        ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-900 shadow-lg shadow-slate-300/40'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                          active
                            ? 'bg-white/20 text-white backdrop-blur-sm'
                            : done
                            ? 'bg-green-50 text-green-600 border border-green-200'
                            : 'bg-slate-100 text-slate-500 border border-slate-200 group-hover:bg-slate-200 group-hover:text-slate-700'
                        }`}
                      >
                        {done ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <div>
                            {tab.icon}
                          </div>
                        )}
                      </div>
                      <span
                        className={`text-sm font-semibold transition-colors ${
                          active
                            ? 'text-white'
                            : done
                            ? 'text-[#0E1B2E]'
                            : 'text-slate-600 group-hover:text-[#0E1B2E]'
                        }`}
                      >
                        {tab.shortLabel}
                      </span>
                    </div>
                  </button>
                </div>
              );
            })}
          </div>

          {user && (
            <div className="flex items-center gap-3 flex-shrink-0 ml-auto">
              <div className="text-right">
                <div className={`${inter.className} text-sm font-semibold text-[#0E1B2E] truncate`}>
                  {user.name || user.username}
                </div>
                <div className={`${inter.className} text-xs text-slate-600 capitalize truncate font-medium`}>
                  {user.role || 'Employee'}
                </div>
              </div>
              <button
                onClick={logout}
                className={`${inter.className} flex items-center gap-2 px-4 py-2.5 rounded-xl hover:bg-slate-50 transition-all text-[#0E1B2E] border-2 border-slate-200 hover:border-slate-300 text-sm font-semibold shadow-sm hover:shadow-md`}
                title="Go Back"
              >
                <ArrowLeft className="w-4 h-4" />
                Go Back
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 mb-4">
          {tabs.map((tab, index) => {
            const currentIndex = tabs.findIndex((t) => t.id === activeTab);
            const isCurrent = index === currentIndex;
            const isCompleted = index < currentIndex;
            const fillPercentage = isCurrent ? 100 : isCompleted ? 100 : 0;

            return (
              <div
                key={tab.id}
                className="flex-1 relative h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60"
              >
                {/* Fill with gradient */}
                <div
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    isCompleted || isCurrent
                      ? 'bg-gradient-to-r from-[#0E1B2E] via-blue-600 to-indigo-600'
                      : 'bg-slate-200'
                  }`}
                  style={{
                    width: `${fillPercentage}%`,
                    boxShadow: isCurrent ? '0 0 12px rgba(59, 130, 246, 0.6)' : 'none',
                  }}
                />

                {/* Glow effect for current section */}
                {isCurrent && (
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 via-blue-500 to-indigo-500 rounded-full opacity-40 animate-pulse" />
                )}

                {/* Section label */}
                <div className={`${inter.className} absolute -bottom-5 left-1/2 -translate-x-1/2 text-xs font-medium whitespace-nowrap transition-colors ${
                  isCurrent
                    ? 'text-blue-600'
                    : isCompleted
                    ? 'text-[#0E1B2E]'
                    : 'text-slate-400'
                }`}>
                  {tab.shortLabel}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Add spacing for labels */}
        <div className="h-4" />
      </div>
    </header>
  );
}