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
import ThreeJsBackground from "@/components/onboarding/ThreeJsBackground";
import { useAuth } from "@/components/auth/AuthContext";

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
  const [darkMode, setDarkMode] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  const router = useRouter();
  const hasRedirected = useRef(false);
  const { login, signup, isAuthenticated, user } = useAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      hasRedirected.current = true;
      setCheckingAuth(false);
      if (user.role === "admin") router.replace("/admin");
      else if (user.role === "manager") router.replace("/manager/tasks");
      else router.replace("/employee/tasks");
    } else {
      setCheckingAuth(false);
    }
  }, [isAuthenticated, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      if (isLogin) {
        const result = await login(username, password);
        if (!result.success) setError(result.error || "Login failed");
      } else {
        const signupData = {
          username,
          password,
          role: selectedRole,
          name: name,
          designation: designation,
          employee_id: employeeId || null,
          managers: [],
          status: "general",
        };
        const result = await signup(signupData);
        if (result.success) {
          setSuccessMsg("Account created successfully! Please login.");
          setIsLogin(true);
          setPassword("");
        } else {
          setError(result.error || "Signup failed");
        }
      }
    } catch (err) {
      console.error(err);
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  if (checkingAuth) {
    return (
      <div
        className={`min-h-screen flex items-center justify-center ${
          darkMode ? "bg-gray-900" : "bg-gray-50"
        }`}
      >
        <Loader message="Loading..." fullScreen={false} />
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen flex items-center justify-center transition-colors duration-700 relative overflow-hidden ${
        darkMode
          ? "bg-gray-900 text-gray-100"
          : "bg-gradient-to-br from-slate-50 to-indigo-50 text-slate-900"
      }`}
      onMouseMove={handleMouseMove}
    >
      <ThreeJsBackground darkMode={darkMode} />
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(99, 102, 241, 0.15) 0%, transparent 50%)`,
        }}
      />
      <div className="w-full max-w-md relative z-10 my-10">
        <div
          className={`rounded-2xl shadow-xl border p-8 backdrop-blur-xl ${
            darkMode
              ? "bg-gray-900/70 border-gray-700"
              : "bg-white/70 border-slate-200"
          }`}
        >
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
              {isLogin ? (
                <Lock className="w-8 h-8 text-white" />
              ) : (
                <UserPlus className="w-8 h-8 text-white" />
              )}
            </div>
            <h1 className="text-2xl font-bold mb-2">
              {isLogin ? "Welcome Back" : "Create Account"}
            </h1>
            <p
              className={`text-sm ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}
            >
              {isLogin
                ? "Enter your credentials to access your account"
                : "Fill in the details to get started"}
            </p>
          </div>
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-300 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}
          {successMsg && (
            <div className="mb-6 p-4 rounded-lg bg-green-900/30 border border-green-700 text-green-300 flex items-center gap-3">
              <p className="text-sm">{successMsg}</p>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Username</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  placeholder="johndoe"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>
            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                      placeholder="John Doe"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Role
                    </label>
                    <select
                      value={selectedRole}
                      onChange={(e) => setSelectedRole(e.target.value)}
                      className={`block w-full px-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all ${
                        darkMode ? "bg-gray-800" : "bg-white"
                      }`}
                    >
                      <option value="employee">Employee</option>
                      <option value="manager">Manager</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Emp ID
                    </label>
                    <div className="relative">
                      <Badge className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
                      <input
                        type="text"
                        value={employeeId}
                        onChange={(e) => setEmployeeId(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="E-123"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Designation
                  </label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
                    <input
                      type="text"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2.5 rounded-lg border bg-transparent focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                      placeholder="Software Engineer"
                    />
                  </div>
                </div>
              </>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-2.5 px-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : isLogin ? (
                <>
                  <LogIn className="w-5 h-5" /> Login
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5" /> Sign Up
                </>
              )}
            </button>
          </form>
          <div className="mt-6 text-center">
            <p
              className={`text-sm ${
                darkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError("");
                  setSuccessMsg("");
                }}
                className="ml-2 font-semibold text-indigo-500 hover:text-indigo-400 transition-colors"
              >
                {isLogin ? "Sign up" : "Login"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function UnifiedLoginPage() {
  return <UnifiedLoginContent />;
}
