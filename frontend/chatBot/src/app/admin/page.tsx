'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminPage from '@/components/admin/page';

export default function Page() {
  return (
    <ProtectedRoute>
      <AdminPage />
    </ProtectedRoute>
  );
}

