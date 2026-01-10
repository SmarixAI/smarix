'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OffboardingEmployeeLayout from '@/components/offboarding/OffboardingEmployeeLayout';

export default function OffboardingEmployeePage() {
  return (
    <ProtectedRoute requiredRole="employee" requiredStatus="offboard">
      <OffboardingEmployeeLayout />
    </ProtectedRoute>
  );
}

