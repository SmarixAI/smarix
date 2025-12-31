'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import EmployeeTasksContent from '@/app/offboarding/employee/tasks/page';

function EmployeeTasksPage() {
  return (
    <AuthProvider>
      <ProtectedRoute requiredRole="employee">
        <EmployeeTasksContent />
      </ProtectedRoute>
    </AuthProvider>
  );
}

export default EmployeeTasksPage;

