'use client';

import { useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth, UserRole } from './AuthContext';
import Loader from '@/components/offboarding/Loader';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  requiredStatus?: 'onboard' | 'offboard' | 'general';
}

export default function ProtectedRoute({ 
  children, 
  requiredRole,
  requiredStatus
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
      return;
    }

    // Check role requirement
    if (requiredRole && user?.role !== requiredRole) {
      if (!hasRedirected.current) {
        hasRedirected.current = true;
        // Redirect based on user role
        if (user?.role === 'manager') {
          router.replace('/manager/dashboard');
        } else if (user?.role === 'admin') {
          router.replace('/admin');
        } else {
          router.replace('/login');
        }
      }
      return;
    }

    // Check status requirement for employee pages
    if (requiredStatus && user) {
      const userStatus = (user.status || 'general').toLowerCase();
      
      // Only check status for employees, not for managers/admins
      if (user.role === 'employee') {
        if (userStatus !== requiredStatus.toLowerCase()) {
          if (!hasRedirected.current) {
            hasRedirected.current = true;
            // Redirect based on actual status
            if (userStatus === 'onboard') {
              router.replace('/employee/onboarding');
            } else if (userStatus === 'offboard') {
              router.replace('/employee/offboarding');
            } else {
              // general status - redirect to chat
              router.replace('/chat');
            }
          }
          return;
        }
      } else {
        // Managers and admins should not access employee onboarding/offboarding pages
        if (pathname?.includes('/employee/onboarding') || pathname?.includes('/employee/offboarding')) {
          if (!hasRedirected.current) {
            hasRedirected.current = true;
            if (user.role === 'manager') {
              router.replace('/manager/dashboard');
            } else if (user.role === 'admin') {
              router.replace('/admin');
            } else {
              router.replace('/login');
            }
          }
          return;
        }
      }
    }
  }, [isAuthenticated, loading, user, requiredRole, requiredStatus, router, pathname]);

  if (loading) {
    return <Loader message="Authenticating..." fullScreen />;
  }

  // CRITICAL FIX: If user is missing, return NULL immediately.
  // This prevents the "Client-side exception" where child components try to access user.name
  if (!isAuthenticated || !user) {
    return null; 
  }

  // Final checks before rendering
  if (requiredRole && user.role !== requiredRole) {
    return null;
  }

  if (requiredStatus && user.role === 'employee') {
    const userStatus = (user.status || 'general').toLowerCase();
    if (userStatus !== requiredStatus.toLowerCase()) {
      return null;
    }
  }

  // Prevent managers/admins from accessing employee onboarding/offboarding pages
  if ((pathname?.includes('/employee/onboarding') || pathname?.includes('/employee/offboarding')) && 
      (user.role === 'manager' || user.role === 'admin')) {
    return null;
  }

  return <>{children}</>;
}