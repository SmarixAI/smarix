'use client';

import { useState, useEffect } from 'react';
import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OffboardingEmployeeLayout from '@/components/offboarding/OffboardingEmployeeLayout';

function OffboardingEmployeePageContent() {
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
    <ProtectedRoute>
      <div className={`min-h-screen transition-colors duration-300 ${
        darkMode 
          ? "bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800" 
          : "bg-gradient-to-br from-slate-50 via-indigo-50/30 to-purple-50/30"
      }`}>
        <OffboardingEmployeeLayout 
          darkMode={darkMode}
          setDarkMode={setDarkMode}
        />
      </div>
    </ProtectedRoute>
  );
}

export default function OffboardingEmployeePage() {
  return (
    <AuthProvider>
      <OffboardingEmployeePageContent />
    </AuthProvider>
  );
}

