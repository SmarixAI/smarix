"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  LogIn,
  Lock,
  User as UserIcon,
  AlertCircle,
  UserPlus,
  Briefcase,
  Badge,
} from "lucide-react";
import Loader from "@/components/offboarding/Loader";
import { useAuth } from "@/components/auth/AuthContext";
import Image from "next/image";

function UnifiedLoginContent() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [designation, setDesignation] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [selectedRole, setSelectedRole] = useState("employee");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const router = useRouter();
  const { login, signup, isAuthenticated, user } = useAuth();

  useEffect(() => {
    // Only check for existing authentication on initial load
    const token = localStorage.getItem("access_token");
    if (token && isAuthenticated && user) {
      // User is already authenticated, redirect immediately
      if (user.role === "admin") router.replace("/admin");
      else if (user.role === "manager") router.replace("/manager/dashboard");
      else router.replace("/chat");
    } else {
      setCheckingAuth(false);
    }
  }, []); // Only run once on mount

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await login(username, password);
        if (res.success) {
          // Get user data from token and redirect immediately
          const token = localStorage.getItem("access_token");
          if (token) {
            try {
              const decoded = JSON.parse(atob(token.split('.')[1]));
              const userRole = decoded.role;
              
              if (userRole === "admin") {
                router.replace("/admin");
              } else if (userRole === "manager") {
                router.replace("/manager/dashboard");
              } else {
                router.replace("/chat");
              }
            } catch (error) {
              console.error("Error parsing token:", error);
              setError("Login successful but failed to redirect. Please refresh the page.");
            }
          } else {
            setError("Login successful but no token found. Please try again.");
          }
        } else {
          setError(res.error || "Login failed");
        }
      } else {
        const res = await signup({
          username,
          password,
          role: selectedRole,
          name,
          designation,
          employee_id: employeeId || null,
          managers: [],
          status: "general",
        });

        if (res.success) {
          setSuccessMsg("Account created. Please login.");
          setIsLogin(true);
        } else {
          setError(res.error || "Signup failed");
        }
      }
    } catch {
      setError("Unexpected error occurred");
    } finally {
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

      <div className="w-full max-w-md rounded-3xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-xl p-8 relative z-10">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-black flex items-center justify-center">
            <Image src="/logo.png" alt="Logo" width={32} height={32} />
          </div>
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-black text-center mb-1">
          {isLogin ? "Sign in with email" : "Create your account"}
        </h1>

        <p className="text-center text-sm text-gray-500 mb-6">
          Make your work life simpler with Smarix
        </p>

        {error && (
          <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {successMsg && (
          <div className="mb-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            icon={<UserIcon size={18} />}
            placeholder="Email or username"
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

          {!isLogin && (
            <>
              <Input
                icon={<UserIcon size={18} />}
                placeholder="Full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />

              <div className="grid grid-cols-2 gap-3">
                <Input
                  icon={<Badge size={18} />}
                  placeholder="Employee ID"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                />
                <select
                  className="rounded-xl px-3 py-3 bg-gray-100 outline-none"
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                >
                  <option value="employee">Employee</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <Input
                icon={<Briefcase size={18} />}
                placeholder="Designation"
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
              />
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 bg-black text-white rounded-xl py-3 font-medium hover:bg-black/90 transition"
          >
            {loading ? "Please wait..." : isLogin ? "Get Started" : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          {isLogin ? "Don’t have an account?" : "Already have an account?"}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="ml-1 font-medium text-black"
          >
            {isLogin ? "Sign up" : "Login"}
          </button>
        </p>
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
