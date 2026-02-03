"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";

export type UserRole = "admin" | "manager" | "employee";

export interface User {
  username: string;
  role: UserRole;
  employeeId?: string | null;
  name?: string;
  designation?: string;
  status?: string;
  schema_name?: string;
  db_identifier?: string;
  // ✅ ADDED: Active Repositories field
  activeRepos?: string[];
}

interface AuthContextType {
  user: User | null;
  login: (
    username: string,
    password: string,
  ) => Promise<{ success: boolean; error?: string }>;
  signup: (userData: any) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function parseJwt(token: string) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join(""),
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // FIX: Simplified initialization logic
  // Removed the 'logout_in_progress' check to prevent loops on refresh
  useEffect(() => {
    const initializeAuth = () => {
      const storedToken = localStorage.getItem("access_token");

      if (storedToken) {
        const decoded = parseJwt(storedToken);

        // Check if token is valid and not expired
        if (decoded && decoded.exp * 1000 > Date.now()) {
          setToken(storedToken);
          setUser({
            username: decoded.sub,
            role: decoded.role as UserRole,
            status: decoded.status,
            employeeId: decoded.employeeId,
            name: decoded.name,
            schema_name: decoded.schema_name,
            db_identifier: decoded.db_identifier,
            // ✅ ADDED: Extract activeRepos from stored token
            activeRepos: decoded.activeRepos || [],
          });
        } else {
          // Token expired or invalid
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (
    username: string,
    password: string,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await fetch(`${API_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "Login failed" };
      }

      const accessToken = data.access_token;
      localStorage.setItem("access_token", accessToken);
      setToken(accessToken);

      const decoded = parseJwt(accessToken);
      const userData: User = {
        username: decoded.sub,
        role: decoded.role,
        status: decoded.status,
        employeeId: decoded.employeeId,
        name: decoded.name,
        schema_name: decoded.schema_name,
        db_identifier: decoded.db_identifier,
        // ✅ ADDED: Extract activeRepos from fresh login token
        activeRepos: decoded.activeRepos || [],
      };

      console.log(userData, "userData");

      setUser(userData);
      localStorage.setItem("user", JSON.stringify(userData));

      // Clear any legacy flags just in case
      sessionStorage.removeItem("logout_in_progress");

      return { success: true };
    } catch (error) {
      console.error("Login error:", error);
      return { success: false, error: "Network error." };
    }
  };

  const signup = async (
    userData: any,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData),
      });
      const data = await response.json();
      if (!response.ok)
        return { success: false, error: data.detail || "Signup failed" };
      return { success: true };
    } catch (error) {
      return { success: false, error: "Network error." };
    }
  };

  const logout = () => {
    // FIX: Removed setting 'logout_in_progress' to avoid stuck loops
    const fromTryProduct = sessionStorage.getItem("from_try_product");
    const redirectPath =
      fromTryProduct === "true" ? "/try-our-product" : "/login";

    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("onboardingActiveTab")

    setUser(null);
    setToken(null);

    if (fromTryProduct === "true") {
      sessionStorage.removeItem("from_try_product");
    }

    // Force immediate redirect using window.location to ensure state is cleared
    window.location.replace(redirectPath);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        loading,
        token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
