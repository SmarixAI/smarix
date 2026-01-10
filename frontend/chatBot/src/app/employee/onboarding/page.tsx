'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OnboardingPage from '@/components/onboarding/page';

export default function OnboardingEmployeePage() {
  return (
    <ProtectedRoute requiredRole="employee" requiredStatus="onboard">
      <OnboardingPage />
    </ProtectedRoute>
  );
}

