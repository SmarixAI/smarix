'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ManagerTasksContent from '@/app/offboarding/manager/tasks/page';

function ManagerTasksPage() {
  return (
    <AuthProvider>
      <ProtectedRoute requiredRole="manager">
        <ManagerTasksContent />
      </ProtectedRoute>
    </AuthProvider>
  );
}

export default ManagerTasksPage;

