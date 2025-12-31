'use client';

import { useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth, UserRole } from './AuthContext';
import Loader from '@/components/offboarding/Loader';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
}

export default function ProtectedRoute({ 
  children, 
  requiredRole 
}: ProtectedRouteProps) {
  const { isAuthenticated, loading, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const hasRedirected = useRef(false);

  useEffect(() => {
    hasRedirected.current = false;
  }, [pathname]);

  useEffect(() => {
    if (loading) return;
    
    // Don't redirect if we are already on login
    if (pathname?.startsWith('/login')) return;

    if (!isAuthenticated) {
      if (!hasRedirected.current) {
        hasRedirected.current = true;
        router.replace('/login');
      }
    } else if (requiredRole && user?.role !== requiredRole) {
      // Special Exception: Managers can view employee pages
      if (pathname?.includes('/employee') && user?.role === 'manager') {
        return;
      }
      
      if (!hasRedirected.current) {
        hasRedirected.current = true;
        router.replace('/login');
      }
    }
  }, [isAuthenticated, loading, user, requiredRole, router, pathname]);

  if (loading) {
    return <Loader message="Authenticating..." fullScreen />;
  }

  // CRITICAL FIX: If user is missing, return NULL immediately.
  // This prevents the "Client-side exception" where child components try to access user.name
  if (!isAuthenticated || !user) {
    return null; 
  }

  if (requiredRole && user.role !== requiredRole) {
     if (pathname?.includes('/employee') && user.role === 'manager') {
        return <>{children}</>;
     }
     return null;
  }

  return <>{children}</>;
}