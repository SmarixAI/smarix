'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { Users, LogOut, FileText, Calendar, User, Moon, Sun, MessageSquare } from 'lucide-react';
import Loader from '@/components/offboarding/Loader';
import ThreeJsBackground from '@/components/onboarding/ThreeJsBackground';

function ManagerDashboardContent() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  useEffect(() => {
    // Redirect to tasks page immediately
    router.replace('/manager/tasks');
  }, [router]);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  const handleOptionClick = (option: string) => {
    if (option === 'onboarding') {
      router.push('/manager/onboarding');
    } else if (option === 'offboarding') {
      router.push('/manager/offboarding');
    } else if (option === 'day-to-day') {
      router.push('/manager/tasks');
    } else if (option === 'chatbot') {
      router.push('/chat');
    }
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-700 relative overflow-hidden ${
        darkMode
          ? "bg-gray-900 text-gray-100"
          : "bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 text-slate-900"
      }`}
      onMouseMove={handleMouseMove}
    >
      <style jsx global>{`
        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-scale-in {
          animation: scaleIn 0.5s ease-out forwards;
        }

        .glass-card-light {
          backdrop-filter: blur(20px) saturate(200%);
          -webkit-backdrop-filter: blur(20px) saturate(200%);
          background: rgba(255, 255, 255, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.5);
        }

        .glass-card-dark {
          backdrop-filter: blur(16px) saturate(180%);
          -webkit-backdrop-filter: blur(16px) saturate(180%);
          background: rgba(17, 24, 39, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
      `}</style>

      <ThreeJsBackground darkMode={darkMode} />

      <div
        className="fixed inset-0 pointer-events-none z-0 transition-all duration-300"
        style={{
          background: darkMode
            ? `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.2) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(139, 92, 246, 0.2) 0%, transparent 50%)`
            : `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(6, 182, 212, 0.15) 0%, transparent 50%)`,
        }}
      />
      {/* HEADER */}
      <header className={`border-b shadow-sm transition-colors duration-300 relative z-10 ${
        darkMode
          ? "glass-card-dark border-gray-700"
          : "glass-card-light border-slate-200"
      }`}>
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${
              darkMode ? "bg-indigo-600" : "bg-indigo-200 text-indigo-700"
            }`}>
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h1 className={`text-2xl font-extrabold tracking-tight ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}>
                Manager Dashboard
              </h1>
              <p className={`text-sm font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Manage your team's activities
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* THEME TOGGLE */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg transition ${
                darkMode
                  ? "hover:bg-gray-800 text-yellow-400"
                  : "hover:bg-indigo-50 text-indigo-600"
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
            {user && (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className={`p-2 rounded-full transition ${
                    darkMode
                      ? "hover:bg-gray-800 text-gray-300"
                      : "hover:bg-indigo-50 text-slate-700"
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
                          {user.name || user.username}
                        </p>
                        <p
                          className={`text-xs ${
                            darkMode ? "text-gray-400" : "text-slate-500"
                          }`}
                        >
                          Manager
                        </p>
                      </div>

                      <div className="p-2 space-y-1">
                        <button
                          onClick={() => {
                            logout();
                            setUserMenuOpen(false);
                          }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                            darkMode
                              ? "hover:bg-gray-800 text-gray-300"
                              : "hover:bg-indigo-50 text-slate-700"
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
      </header>

      {/* MAIN CONTENT */}
      <div className="max-w-screen-2xl mx-auto px-6 py-12 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* MANAGE ONBOARDING */}
          <div
            onClick={() => handleOptionClick('onboarding')}
            className={`group relative rounded-2xl shadow-lg border-2 p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-105 animate-scale-in ${
              darkMode
                ? "glass-card-dark border-gray-700 hover:border-indigo-500"
                : "glass-card-light border-slate-200 hover:border-indigo-500"
            }`}
            style={{ animationDelay: '0.1s' }}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform ${
                darkMode
                  ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                  : "bg-gradient-to-br from-indigo-500 to-purple-600"
              }`}>
                <Users className="w-8 h-8 text-white" />
              </div>
              <h2 className={`text-xl font-bold mb-2 ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}>
                Manage Onboarding
              </h2>
              <p className={`text-sm mb-4 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Set up and manage employee onboarding processes
              </p>
            </div>
          </div>

          {/* MANAGE OFFBOARDING */}
          <div
            onClick={() => handleOptionClick('offboarding')}
            className={`group relative rounded-2xl shadow-lg border-2 p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-105 animate-scale-in ${
              darkMode
                ? "glass-card-dark border-gray-700 hover:border-indigo-500"
                : "glass-card-light border-slate-200 hover:border-indigo-500"
            }`}
            style={{ animationDelay: '0.2s' }}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform ${
                darkMode
                  ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                  : "bg-gradient-to-br from-indigo-500 to-purple-600"
              }`}>
                <LogOut className="w-8 h-8 text-white" />
              </div>
              <h2 className={`text-xl font-bold mb-2 ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}>
                Manage Offboarding
              </h2>
              <p className={`text-sm mb-4 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Handle employee offboarding and exit processes
              </p>
            </div>
          </div>

          {/* MANAGE DAY TO DAY TASK */}
          <div
            onClick={() => handleOptionClick('day-to-day')}
            className={`group relative rounded-2xl shadow-lg border-2 p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-105 animate-scale-in ${
              darkMode
                ? "glass-card-dark border-gray-700 hover:border-indigo-500"
                : "glass-card-light border-slate-200 hover:border-indigo-500"
            }`}
            style={{ animationDelay: '0.3s' }}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform ${
                darkMode
                  ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                  : "bg-gradient-to-br from-indigo-500 to-purple-600"
              }`}>
                <Calendar className="w-8 h-8 text-white" />
              </div>
              <h2 className={`text-xl font-bold mb-2 ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}>
                Manage Day to Day Task
              </h2>
              <p className={`text-sm mb-4 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Track and manage daily team tasks and activities
              </p>
            </div>
          </div>

          {/* GENERAL CHATBOT */}
          <div
            onClick={() => handleOptionClick('chatbot')}
            className={`group relative rounded-2xl shadow-lg border-2 p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-105 animate-scale-in ${
              darkMode
                ? "glass-card-dark border-gray-700 hover:border-indigo-500"
                : "glass-card-light border-slate-200 hover:border-indigo-500"
            }`}
            style={{ animationDelay: '0.4s' }}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform ${
                darkMode
                  ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                  : "bg-gradient-to-br from-indigo-500 to-purple-600"
              }`}>
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h2 className={`text-xl font-bold mb-2 ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}>
                General Chatbot
              </h2>
              <p className={`text-sm mb-4 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Get help and answers from the AI assistant
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ManagerDashboardPage() {
  return (
    <AuthProvider>
      <ProtectedRoute requiredRole="manager">
        <ManagerDashboardContent />
      </ProtectedRoute>
    </AuthProvider>
  );
}

