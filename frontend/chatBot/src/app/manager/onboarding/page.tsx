'use client';

import { useState, useEffect } from 'react';
import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OnboardingManagerLayout from '@/components/onboarding/OnboardingManagerLayout';
import ThreeJsBackground from '@/components/onboarding/ThreeJsBackground';

function OnboardingManagerPageContent() {
  const [darkMode, setDarkMode] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  // Dark mode effect
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

  return (
    <ProtectedRoute requiredRole="manager">
      <div
        className={`min-h-screen transition-colors duration-700 relative overflow-hidden ${
          darkMode
            ? "bg-gray-900 text-gray-100"
            : "bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 text-slate-900"
        }`}
        onMouseMove={handleMouseMove}
      >
        <style jsx global>{`
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

        <div className="relative z-10">
          <OnboardingManagerLayout 
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default function OnboardingManagerPage() {
  return (
    <AuthProvider>
      <OnboardingManagerPageContent />
    </AuthProvider>
  );
}

