'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OnboardingPage from '@/components/onboarding/page';

function OnboardingPageContent() {
  return (
    <ProtectedRoute requiredRole="employee" requiredStatus="onboard">
      <OnboardingPage />
    </ProtectedRoute>
  );
}

export default function OnboardingEmployeePage() {
  return (
    <AuthProvider>
      <OnboardingPageContent />
    </AuthProvider>
  );
}

