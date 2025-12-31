'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Loader from '@/components/offboarding/Loader';

export default function OffboardingPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to employee login (used for both managers and employees)
    router.push('/login');
  }, [router]);

  return <Loader message="Redirecting..." fullScreen />;
}

