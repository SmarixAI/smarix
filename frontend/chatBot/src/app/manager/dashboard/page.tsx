'use client';

import { useState, useEffect } from 'react';
import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import UnifiedDashboard from '@/components/manager/UnifiedDashboard';

function ManagerDashboardPageContent() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <ProtectedRoute requiredRole="manager">
      <UnifiedDashboard darkMode={darkMode} setDarkMode={setDarkMode} />
    </ProtectedRoute>
  );
}

export default function ManagerDashboardPage() {
  return (
    <AuthProvider>
      <ManagerDashboardPageContent />
    </AuthProvider>
  );
}

