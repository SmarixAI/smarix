'use client';

import { useState, useEffect } from 'react';
import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OnboardingManagerLayout from '@/components/onboarding/OnboardingManagerLayout';

function OnboardingManagerPageContent() {
  const [darkMode, setDarkMode] = useState(false);

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <ProtectedRoute requiredRole="manager">
      <div className={`min-h-screen transition-colors duration-300 ${
        darkMode 
          ? "bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800" 
          : "bg-gradient-to-br from-slate-50 via-indigo-50/30 to-purple-50/30"
      }`}>
        <OnboardingManagerLayout 
          darkMode={darkMode}
          setDarkMode={setDarkMode}
        />
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

