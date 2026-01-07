'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Loader from '@/components/offboarding/Loader';

export default function OnboardingManagerPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to unified dashboard
    router.replace('/manager/dashboard');
  }, [router]);

  return <Loader message="Redirecting to dashboard..." fullScreen />;
}

