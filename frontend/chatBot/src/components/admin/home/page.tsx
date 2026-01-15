import { Features } from '@/components/landing/Features';
import { Footer } from '@/components/landing/Footer';
import { Hero } from '@/components/landing/Hero';
import { Navbar } from '@/components/landing/Navbar';
import { Process } from '@/components/landing/Process';
import { Transition } from '@/components/landing/Transition';
import React from 'react';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white"> 
      <Navbar />
      <Hero />
      <Process /> 
      <Transition />
      <Features />
      <Footer />
    </main>
  );
}