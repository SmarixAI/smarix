'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OffboardingEmployeeLayout from '@/components/offboarding/OffboardingEmployeeLayout';

function OffboardingEmployeePageContent() {
  return (
    <ProtectedRoute requiredRole="employee" requiredStatus="offboard">
      <OffboardingEmployeeLayout />
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

