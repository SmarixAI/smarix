'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import UnifiedDashboard from '@/components/manager/UnifiedDashboard';

export default function ManagerDashboardPage() {
  return (
    <ProtectedRoute requiredRole="manager">
      <UnifiedDashboard />
    </ProtectedRoute>
  );
}

