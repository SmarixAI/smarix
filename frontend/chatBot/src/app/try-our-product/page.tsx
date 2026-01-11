'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/landing/Navbar';
import { ArrowRight, UserPlus, UserMinus, Users, MessageSquare, Sparkles, Loader2 } from 'lucide-react';
import { Fira_Code, Victor_Mono } from 'next/font/google';
import { useAuth } from '@/components/auth/AuthContext';

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const victorMono = Victor_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

const roles = [
  {
    id: 'onboarding-employee',
    title: 'Onboarding Employee',
    description: 'Experience our AI-powered onboarding system. Get personalized learning paths, interactive tutorials, and seamless knowledge transfer.',
    icon: UserPlus,
    username: 'Mastermind-sap',
    password: 'Mastermind-sap',
    requiresAuth: true,
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-600',
  },
  {
    id: 'offboarding-employee',
    title: 'Offboarding Employee',
    description: 'Streamline your exit process. Capture knowledge, create handovers, and ensure smooth transitions for your team.',
    icon: UserMinus,
    username: 'SahilDWanjare',
    password: 'SahilDWanjare',
    requiresAuth: true,
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    iconColor: 'text-purple-600',
  },
  {
    id: 'manager',
    title: 'Manager',
    description: 'Manage onboarding and offboarding processes for your team. Track progress, assign tasks, and oversee knowledge transfer.',
    icon: Users,
    username: 'manager1',
    password: 'manager1',
    requiresAuth: true,
    color: 'from-indigo-500 to-purple-500',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    iconColor: 'text-indigo-600',
  },
  {
    id: 'ai-assistant',
    title: 'AI Assistant',
    description: 'Access our intelligent chatbot for any project-related queries. Get instant answers, code insights, and technical guidance.',
    icon: MessageSquare,
    requiresAuth: false,
    route: '/chat',
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    iconColor: 'text-emerald-600',
  },
];

export default function TryOurProductPage() {
  const router = useRouter();
  const { login, user } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);
  const [pendingRedirect, setPendingRedirect] = useState<string | null>(null);

  // Handle redirect after user state updates
  useEffect(() => {
    if (pendingRedirect && user) {
      const redirectPath = pendingRedirect;
      setPendingRedirect(null);
      router.replace(redirectPath);
    }
  }, [user, pendingRedirect, router]);

  const getRedirectPath = (userData: any): string => {
    if (userData.role === 'manager') {
      return '/manager/dashboard';
    } else if (userData.role === 'employee') {
      const status = (userData.status || 'general').toLowerCase();
      if (status === 'onboard') {
        return '/employee/onboarding';
      } else if (status === 'offboard') {
        return '/employee/offboarding';
      } else {
        return '/chat';
      }
    }
    return '/chat';
  };

  const handleRoleClick = async (role: typeof roles[0]) => {
    // If no auth required (AI Assistant), just redirect
    if (!role.requiresAuth && role.route) {
      router.push(role.route);
      return;
    }

    // For roles requiring auth, login and redirect
    if (!role.username || !role.password) return;

    // Store that user came from try-our-product page
    sessionStorage.setItem("from_try_product", "true");

    setLoading(role.id);

    try {
      const result = await login(role.username, role.password);
      
      if (result.success) {
        // Get user from localStorage immediately (login sets it)
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const userData = JSON.parse(userStr);
          const redirectPath = getRedirectPath(userData);
          setPendingRedirect(redirectPath);
        } else {
          // Fallback: wait a bit for context to update
          setTimeout(() => {
            const userStr = localStorage.getItem('user');
            if (userStr) {
              const userData = JSON.parse(userStr);
              router.replace(getRedirectPath(userData));
            }
            setLoading(null);
          }, 200);
        }
      } else {
        alert(result.error || 'Login failed');
        setLoading(null);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('An error occurred during login');
      setLoading(null);
    }
  };

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      <div className="relative w-full pt-32 pb-24 px-6 overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 mb-6"
            >
              <Sparkles className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Choose Your Role
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Try Our Product
            </h1>
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed`}>
              Select a role to explore Smarix from different perspectives. Experience how we streamline knowledge transfer and enhance productivity.
            </p>
          </motion.div>

          {/* Role Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-6xl mx-auto">
            {roles.map((role, index) => {
              const Icon = role.icon;
              return (
                <motion.div
                  key={role.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  whileHover={loading === role.id ? {} : { scale: 1.02, y: -5 }}
                  className={`group relative ${loading === role.id ? 'cursor-wait opacity-75' : 'cursor-pointer'}`}
                  onClick={() => !loading && handleRoleClick(role)}
                >
                  <div className={`
                    relative h-full rounded-2xl border-2 ${role.borderColor} ${role.bgColor}
                    p-8 transition-all duration-300
                    hover:shadow-2xl hover:shadow-black/10
                    overflow-hidden
                  `}>
                    {/* Gradient Overlay on Hover */}
                    <div className={`
                      absolute inset-0 bg-gradient-to-br ${role.color} opacity-0
                      group-hover:opacity-5 transition-opacity duration-300
                    `} />
                    
                    {/* Icon */}
                    <div className="mb-6 relative z-10">
                      <div className={`
                        w-14 h-14 rounded-xl ${role.bgColor} border-2 ${role.borderColor}
                        flex items-center justify-center
                        group-hover:scale-110 transition-transform duration-300
                      `}>
                        <Icon className={`w-7 h-7 ${role.iconColor}`} />
                      </div>
                    </div>

                    {/* Content */}
                    <div className="relative z-10">
                      <h3 className={`
                        ${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-3
                        group-hover:translate-x-1 transition-transform duration-300
                      `}>
                        {role.title}
                      </h3>
                      <p className={`
                        ${victorMono.className} text-base text-[#0E1B2E]/70 leading-relaxed mb-6
                      `}>
                        {role.description}
                      </p>

                      {/* CTA Button */}
                      <div className="flex items-center gap-2 text-[#0E1B2E] group-hover:gap-3 transition-all duration-300">
                        {loading === role.id ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span className={`${firaCode.className} text-sm font-semibold tracking-wide`}>
                              Connecting...
                            </span>
                          </>
                        ) : (
                          <>
                            <span className={`${firaCode.className} text-sm font-semibold tracking-wide`}>
                              Get Started
                            </span>
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
                          </>
                        )}
                      </div>
                    </div>

                    {/* Decorative Corner */}
                    <div className={`
                      absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${role.color}
                      opacity-5 rounded-bl-full transform translate-x-8 -translate-y-8
                      group-hover:opacity-10 transition-opacity duration-300
                    `} />
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mt-16 text-center"
          >
            <p className={`${victorMono.className} text-sm text-[#0E1B2E]/50`}>
              Click on any role to automatically sign in and explore Smarix.
            </p>
          </motion.div>
        </div>
      </div>
    </main>
  );
}

