'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sun, Moon, BookOpen, Users, Code, Wrench, Check, Lock, User, LogOut } from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  activeTab: string;
  setActiveTab: (value: string) => void;
}

export default function Header({ darkMode, setDarkMode, activeTab, setActiveTab }: HeaderProps) {
  const router = useRouter();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  // Get user from localStorage
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (e) {
        console.error('Error parsing user data:', e);
      }
    }
  }, []);

  const handleLogout = () => {
    try {
      // Clear user data from localStorage
      localStorage.removeItem('user');
      setUser(null);
      setUserMenuOpen(false);
      
      // Redirect to main login page
      router.push('/login');
    } catch (error) {
      console.error('Error during logout:', error);
      // Fallback: just clear localStorage and reload
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  };
  const handleMagneticMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px) scale(1.05)`;
  };

  const handleMagneticLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.transform = 'translate(0, 0) scale(1)';
  };

  const tabs = [
    { id: 'reading', label: 'Reading & Overview', shortLabel: 'Reading & Overview', icon: <BookOpen className="w-4 h-4" />, step: 1 },
    { id: 'qa', label: 'Q&A Session', shortLabel: 'Q&A Session', icon: <Users className="w-4 h-4" />, step: 2 },
    { id: 'practice', label: 'Practice Tasks', shortLabel: 'Practice Tasks', icon: <Code className="w-4 h-4" />, step: 3 },
    { id: 'bugfix', label: 'Bug Fixing', shortLabel: 'Bug Fixing', icon: <Wrench className="w-4 h-4" />, step: 4 },
  ];

  const getStepStatus = (tabId: string) => {
    const index = tabs.findIndex((t) => t.id === tabId);
    const activeIndex = tabs.findIndex((t) => t.id === activeTab);
    if (index < activeIndex) return 'completed';
    if (index === activeIndex) return 'current';
    return 'available';
  };

  return (
    <header
      className={`sticky top-0 z-50 transition-all ${
        darkMode
          ? 'glass-card-dark border-b border-gray-700'
          : 'glass-card-light border-b border-indigo-100'
      }`}
    >
      {/* ===================== TOP ROW ===================== */}
      <div className="max-w-[1800px] mx-auto px-6 py-3 flex items-center justify-between">

        {/* LEFT — LOGO + TITLE */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-xl relative overflow-hidden ${
              darkMode
                ? 'bg-gradient-to-br from-blue-500 via-purple-600 to-pink-500'
                : 'bg-gradient-to-br from-indigo-500 via-cyan-500 to-teal-500'
            }`}
          >
            <div className="absolute inset-0 shimmer-effect" />
            <BookOpen className="w-6 h-6 text-white relative z-10" />
          </div>

          <div>
            <h1
              className={`text-xl font-bold ${
                darkMode
                  ? 'bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent'
                  : 'bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent'
              }`}
            >
              Onboarding Hub
            </h1>

            <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
              Your personalized learning roadmap • Step{' '}
              {tabs.findIndex((t) => t.id === activeTab) + 1} of {tabs.length}
            </p>
          </div>
        </div>

        {/* RIGHT — DARK MODE & USER */}
        <div className="flex items-center space-x-4 flex-shrink-0">
          {/* THEME TOGGLE */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            onMouseMove={handleMagneticMove}
            onMouseLeave={handleMagneticLeave}
            className={`p-2.5 rounded-xl transition-all shadow-md ${
              darkMode ? 'bg-gray-700/80 hover:bg-gray-600/80' : 'bg-white/80 hover:bg-indigo-50/80'
            }`}
          >
            {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-indigo-600" />}
          </button>

          {/* USER MENU */}
          {user && (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className={`p-2 rounded-full transition ${
                  darkMode
                    ? 'hover:bg-gray-800 text-gray-300'
                    : 'hover:bg-indigo-50 text-slate-700'
                }`}
              >
                <User className="w-5 h-5" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setUserMenuOpen(false)}
                  />

                  <div
                    className={`absolute right-0 mt-2 w-52 rounded-xl border shadow-xl z-20 ${
                      darkMode
                        ? 'glass-card-dark border-gray-700'
                        : 'glass-card-light border-slate-200'
                    }`}
                  >
                    <div className={`px-4 py-3 border-b ${darkMode ? 'border-gray-700' : 'border-slate-200'}`}>
                      <p
                        className={`text-sm font-medium ${
                          darkMode ? 'text-white' : 'text-slate-900'
                        }`}
                      >
                        {user.name || user.username}
                      </p>
                      <p
                        className={`text-xs ${
                          darkMode ? 'text-gray-400' : 'text-slate-500'
                        }`}
                      >
                        Employee
                      </p>
                    </div>

                    <div className="p-2 space-y-1">
                      <button
                        onClick={handleLogout}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                          darkMode
                            ? 'hover:bg-gray-800 text-gray-300'
                            : 'hover:bg-indigo-50 text-slate-700'
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
          )}
        </div>
      </div>

      {/* ===================== PROGRESS BAR SECTION ===================== */}
      <div className="max-w-[1800px] mx-auto px-6 pb-4">
        <div className="relative">

          {/* Background bar */}
          <div
            className={`absolute top-4 left-0 right-0 h-1 ${
              darkMode ? 'bg-gray-700/50' : 'bg-indigo-100/50'
            } rounded-full`}
            style={{ marginLeft: '2rem', marginRight: '2rem' }}
          />

          {/* Smooth progress line */}
          <div
            className={`absolute top-4 left-0 h-1 rounded-full transition-all duration-1000 ease-out ${
              darkMode ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500' : 'bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500'
            }`}
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
                      className={`w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all ${
                        active
                          ? darkMode
                            ? 'bg-gradient-to-br from-blue-500 to-purple-600 ring-4 ring-blue-400/30 scale-110'
                            : 'bg-gradient-to-br from-indigo-500 to-cyan-500 ring-4 ring-indigo-400/30 scale-110'
                          : done
                          ? 'bg-green-500 text-white'
                          : darkMode
                          ? 'bg-gray-700 border border-gray-600'
                          : 'bg-slate-200 border border-slate-300'
                      }`}
                    >
                      {done ? <Check className="w-5 h-5 text-white" /> : tab.icon}
                    </div>

                    {/* Step number badge */}
                    <div
                      className={`absolute -top-1 -right-1 w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center ${
                        active
                          ? 'bg-pink-500 text-white'
                          : done
                          ? 'bg-green-500 text-white'
                          : darkMode
                          ? 'bg-gray-600 text-gray-300'
                          : 'bg-slate-300 text-slate-600'
                      }`}
                    >
                      {tab.step}
                    </div>
                  </div>

                  <p
                    className={`text-xs font-semibold leading-tight ${
                      active
                        ? darkMode
                          ? 'text-blue-400'
                          : 'text-indigo-600'
                        : done
                        ? darkMode
                          ? 'text-green-300'
                          : 'text-green-600'
                        : darkMode
                        ? 'text-gray-500'
                        : 'text-slate-500'
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