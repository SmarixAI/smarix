'use client';

import { useState, useEffect } from 'react';
import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import OffboardingEmployeeLayout from '@/components/offboarding/OffboardingEmployeeLayout';
import ThreeJsBackground from '@/components/onboarding/ThreeJsBackground';

function OffboardingEmployeePageContent() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <OffboardingEmployeeLayout />
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

