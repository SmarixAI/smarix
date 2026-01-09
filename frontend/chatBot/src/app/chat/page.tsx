'use client';

import { AuthProvider } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ChatPage from '@/components/admin/chat/page';

function ChatPageContent() {
  return (
    <ProtectedRoute requiredStatus="general">
      <ChatPage />
    </ProtectedRoute>
  );
}

export default function ChatPageWrapper() {
  return (
    <AuthProvider>
      <ChatPageContent />
    </AuthProvider>
  );
}

