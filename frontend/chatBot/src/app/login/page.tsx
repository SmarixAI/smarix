"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Lock,
  User as UserIcon,
  AlertCircle,
} from "lucide-react";
import Loader from "@/components/offboarding/Loader";
import { useAuth } from "@/components/auth/AuthContext";
import Image from "next/image";

function UnifiedLoginContent() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [shouldRedirect, setShouldRedirect] = useState(false);
  const hasRedirectedRef = useRef(false);

  const router = useRouter();
  const { login, isAuthenticated, user, loading: authLoading } = useAuth();

  const redirectBasedOnUser = useCallback((userData: typeof user) => {
    if (!userData || hasRedirectedRef.current) return;
    
    hasRedirectedRef.current = true;
    
    if (userData.role === "admin") {
      router.replace("/admin");
    } else if (userData.role === "manager") {
      router.replace("/manager/dashboard");
    } else if (userData.role === "employee") {
      // Check employee status and redirect accordingly
      const status = (userData.status || "general").toLowerCase();
      if (status === "onboard") {
        router.replace("/employee/onboarding");
      } else if (status === "offboard") {
        router.replace("/employee/offboarding");
      } else {
        router.replace("/chat");
      }
    } else {
      router.replace("/chat");
    }
  }, [router]);

  // Reset redirect ref when component mounts
  useEffect(() => {
    hasRedirectedRef.current = false;
  }, []);

  // Check for existing authentication on initial load
  useEffect(() => {
    if (!authLoading) {
      const token = localStorage.getItem("access_token");
      if (token && isAuthenticated && user) {
        redirectBasedOnUser(user);
      } else {
        setCheckingAuth(false);
      }
    }
  }, [authLoading, isAuthenticated, user, redirectBasedOnUser]);

  // Handle redirect after successful login - wait for user state to update
  useEffect(() => {
    if (shouldRedirect && user && isAuthenticated && !authLoading) {
      // Verify token exists before redirecting
      const token = localStorage.getItem("access_token");
      if (token) {
        redirectBasedOnUser(user);
        setShouldRedirect(false);
      } else {
        // Token not found, reset and show error
        setError("Authentication failed. Please try again.");
        setShouldRedirect(false);
        setLoading(false);
      }
    }
  }, [shouldRedirect, user, isAuthenticated, authLoading, redirectBasedOnUser]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await login(username, password);
      if (res.success) {
        // Set flag to trigger redirect after auth state updates
        setShouldRedirect(true);
      } else {
        setError(res.error || "Login failed");
        setLoading(false);
      }
    } catch {
      setError("Unexpected error occurred");
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader message="Loading..." />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white overflow-hidden flex items-center justify-center px-4">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

      <div className="w-full max-w-md h-[60vh] rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-xl p-8 relative z-10">
        {/* Logo */}
        <div className="flex justify-center mb-10">
          <div className="w-20 h-20 rounded-2xl bg-black flex items-center justify-center">
            <Image src="/logo.png" alt="Logo" width={50} height={50} />
          </div>
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-black text-center mb-1">
          Sign in to Smarix
        </h1>

        <p className="text-center text-sm text-gray-500 mb-4">
          Make your work life simpler with Smarix
        </p>

        {error && (
          <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8 mt-10">
          <Input
            icon={<UserIcon size={18} />}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <Input
            icon={<Lock size={18} />}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 bg-black text-white rounded-xl py-3 font-medium hover:bg-black/90 transition"
          >
            {loading ? "Please wait..." : "Log In"}
          </button>
        </form>
      </div>

      {/* Simple Footer */}
      <footer className="absolute bottom-4 left-0 right-0 mx-auto w-[92%] md:w-[85%] lg:w-[1000px] bg-white/35 backdrop-blur-xl shadow-md shadow-black/5 border border-white/30 rounded-full px-6 py-3 flex items-center justify-center">
        <div className="text-sm text-[#0E1B2E]/70">
          © 2026 Smarix. All rights reserved.
        </div>
      </footer>
    </main>
  );
}

/* ---------- Reusable Input ---------- */

function Input({
  icon,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 bg-gray-100 rounded-xl px-3 py-3">
      <div className="text-gray-400">{icon}</div>
      <input
        {...props}
        className="bg-transparent w-full outline-none text-sm"
      />
    </div>
  );
}

export default function UnifiedLoginPage() {
  return <UnifiedLoginContent />;
}
