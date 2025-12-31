'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminPage from '@/components/admin/page';

export default function Page() {
  return (
    <AuthProvider>
      <ProtectedRoute>
        <AdminPage />
      </ProtectedRoute>
    </AuthProvider>
  );
}

