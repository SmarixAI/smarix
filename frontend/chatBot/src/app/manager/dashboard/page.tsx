'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import UnifiedDashboard from '@/components/manager/UnifiedDashboard';

function ManagerDashboardPageContent() {
  return (
    <ProtectedRoute requiredRole="manager">
      <UnifiedDashboard />
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

