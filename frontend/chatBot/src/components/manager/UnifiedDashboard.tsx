"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Users,
  User,
  ArrowLeft,
  Search,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle,
  TrendingUp,
  Settings,
  Activity,
  BarChart3,
  LogOut,
  MoreVertical,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import {
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  Area,
  AreaChart,
} from "recharts";
import Loader from "../offboarding/Loader";
import Image from "next/image";
import FinalCallSection from "../offboarding/managerViewSections/FinalCallSection";
import HandoverSection from "../offboarding/managerViewSections/HandoverSection";
import DocumentationSection from "../offboarding/managerViewSections/DocumentationSection";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-inter",
});

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ================= TYPES ================= */

type Employee = {
  id: string;
  employeeId: string;
  name: string;
  role: string;
  username: string;
  status: "onboard" | "offboard";
  profilePicture?: string;
  active_repos?: string[];
  designation?: string;
};

type SectionProgress = {
  section: string;
  status: "Pending" | "Completed";
  expectedHours: number;
  spentHours: number | null;
  completion: number;
  value?: number;
};

type EmployeeProgress = {
  employeeId: string;
  employeeName: string;
  employeeRole?: string;
  type: "onboarding" | "offboarding";
  pendingSections: number;
  completedSections: number;
  efficiency: number;
  overallProgress: number;
  sections: SectionProgress[];
  timeSpentData: { section: string; expected: number; spent: number }[];
  qnaScore?: number;
  qnaTotalQuestions?: number;
  activeRepos?: string[];
  timeToProductivity?: { day: number; productivity: number }[];
};

/* ================= UI HELPERS ================= */

// Custom Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/90 backdrop-blur-md border border-slate-200 p-3 rounded-xl shadow-xl z-50">
        <p className="text-[10px] font-bold text-slate-500 mb-2 uppercase tracking-wider">
          {label}
        </p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 mb-1 last:mb-0">
            <div
              className="w-2 h-2 rounded-full ring-2 ring-white"
              style={{ backgroundColor: entry.color || entry.fill }}
            />
            <span className="text-xs text-slate-600 font-medium capitalize">
              {entry.name}:
            </span>
            <span className="text-xs font-bold text-slate-900 font-mono">
              {typeof entry.value === "number"
                ? Math.round(entry.value)
                : entry.value}
              {entry.unit || ""}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function UnifiedDashboard() {
  const { user, logout, token } = useAuth();
  const [onboardingEmployees, setOnboardingEmployees] = useState<Employee[]>(
    []
  );
  const [offboardingEmployees, setOffboardingEmployees] = useState<Employee[]>(
    []
  );
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(
    null
  );
  const [employeeProgress, setEmployeeProgress] =
    useState<EmployeeProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [onboardingExpanded, setOnboardingExpanded] = useState(true);
  const [offboardingExpanded, setOffboardingExpanded] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [manageOffboardingMode, setManageOffboardingMode] = useState(false);
  const [activeOffboardingSection, setActiveOffboardingSection] = useState<
    "finalcall" | "handover" | "documentation"
  >("finalcall");

  // Initial render log
  useEffect(() => {
    console.log("🚀 UnifiedDashboard component mounted/rendered");
    console.log("Initial user:", user);
    console.log("Initial token:", token ? "exists" : "missing");
  }, []);

  // Reset manage offboarding mode when employee changes
  useEffect(() => {
    setManageOffboardingMode(false);
    setActiveOffboardingSection("finalcall");
  }, [selectedEmployee]);

  // Fetch employees
  useEffect(() => {
    console.log("=== UnifiedDashboard useEffect triggered ===");
    console.log("User object:", user);
    console.log("Token exists:", !!token);

    const fetchEmployees = async () => {
      try {
        console.log("=== Starting fetchEmployees ===");

        // Get manager's employeeId - try both employeeId and employee_id (if present)
        const managerId = user?.employeeId || (user as any)?.employee_id;

        console.log("Manager ID extracted:", managerId);
        console.log("Full user object:", JSON.stringify(user, null, 2));

        if (!managerId || !token) {
          console.error("❌ Missing managerId or token:", {
            managerId,
            hasToken: !!token,
            user,
            employeeId: user?.employeeId,
            employee_id: (user as any)?.employee_id,
          });
          setLoading(false);
          return;
        }

        console.log("✅ Fetching employees for manager:", managerId);
        console.log("API URL:", `${API_URL}/auth/users`);

        const response = await fetch(`${API_URL}/auth/users`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        console.log("Response status:", response.status);
        console.log("Response ok:", response.ok);

        if (!response.ok) {
          const errorText = await response.text();
          console.error(
            "❌ Failed to fetch users:",
            response.status,
            errorText
          );
          setLoading(false);
          return;
        }

        const allUsers = await response.json();
        console.log("=== DEBUG: Employee Filtering ===");
        console.log("All users from API:", allUsers.length);
        console.log("Manager ID:", managerId);
        console.log("Manager user object:", JSON.stringify(user, null, 2));

        // Log all employee users to see their structure
        const allEmployees = allUsers.filter(
          (u: any) => (u.role || "").toLowerCase() === "employee"
        );
        console.log("Total employees found:", allEmployees.length);
        console.log(
          "All employees:",
          allEmployees.map((u: any) => ({
            username: u.username,
            status: u.status,
            employeeId: u.employeeId || u.employee_id,
            managers: u.managers,
            name: u.name,
          }))
        );

        // Filter employees managed by this manager
        const filtered = allUsers.filter((u: any) => {
          const role = (u.role || "").toLowerCase();
          const managers = u.managers || [];

          // Get employee's employeeId (backend uses employee_id, but check both)
          const employeeId = u.employee_id || u.employeeId;

          const isEmployee = role === "employee";

          // Check if manager's ID is in the employee's managers array
          // Also handle case where managers might be stored as strings or IDs
          const isManagedByMe =
            Array.isArray(managers) &&
            (managers.includes(managerId) ||
              managers.some((m: any) => String(m) === String(managerId)));

          if (isEmployee) {
            console.log(`Employee ${u.username || "unknown"}:`, {
              role,
              status: u.status,
              employeeId,
              managers,
              managersArray: JSON.stringify(managers),
              managersTypes: managers.map((m: any) => typeof m),
              isManagedByMe,
              managerId,
              managerIdType: typeof managerId,
              directInclude: managers.includes(managerId),
              stringCompare: managers.some(
                (m: any) => String(m) === String(managerId)
              ),
              statusType: typeof u.status,
              statusLower: (u.status || "").toLowerCase(),
            });
          }

          return isEmployee && isManagedByMe;
        });

        console.log("Filtered employees (by manager):", filtered.length);
        console.log(
          "Filtered employees list:",
          filtered.map((u: any) => ({
            username: u.username,
            status: u.status,
            name: u.name,
          }))
        );

        // Separate onboarding and offboarding employees
        console.log("=== STATUS CHECKING ===");
        filtered.forEach((u: any) => {
          const rawStatus = u.status;
          const normalizedStatus = (rawStatus || "").toLowerCase().trim();
          console.log(
            `Employee ${
              u.username
            }: rawStatus="${rawStatus}" (type: ${typeof rawStatus}), normalized="${normalizedStatus}"`
          );
        });

        const onboarding = filtered
          .filter((u: any) => {
            const status = (u.status || "").toLowerCase().trim();
            const result = status === "onboard";
            if (result) {
              console.log(
                `✓ Onboarding: ${u.username} - status: "${u.status}" (normalized: "${status}")`
              );
            }
            return result;
          })
          .map((u: any) => {
            const employeeId = u.employee_id || u.employeeId || u.username;
            return {
              id: employeeId,
              employeeId: employeeId,
              name: u.name || u.username,
              role: u.designation || u.role || "Employee",
              username: u.username,
              status: "onboard" as const,
              profilePicture: u.profilePicture,
              active_repos: u.active_repos || [],
              designation: u.designation,
            };
          });

        const offboarding = filtered
          .filter((u: any) => {
            const rawStatus = u.status;
            const status = (rawStatus || "").toLowerCase().trim();

            // Check multiple possible values for offboarding status
            const isOffboarding =
              status === "offboard" ||
              status === "offboarding" ||
              status === "off-boarding" ||
              status === "leaving" ||
              (status && status.includes("offboard"));

            console.log(
              `🔍 Checking offboarding for ${u.username || "unknown"}:`
            );
            console.log(
              `   - Raw status: "${rawStatus}" (type: ${typeof rawStatus})`
            );
            console.log(`   - Normalized: "${status}"`);
            console.log(`   - Match "offboard": ${status === "offboard"}`);
            console.log(`   - Is offboarding (flexible): ${isOffboarding}`);
            console.log(`   - Full user object:`, JSON.stringify(u, null, 2));

            if (!isOffboarding && rawStatus) {
              console.warn(
                `   ⚠️ Status "${rawStatus}" does not match offboarding criteria`
              );
            }

            return isOffboarding;
          })
          .map((u: any) => {
            const employeeId = u.employee_id || u.employeeId || u.username;
            console.log(
              `✓ Mapping offboarding employee: ${u.username} -> ${employeeId}`
            );
            return {
              id: employeeId,
              employeeId: employeeId,
              name: u.name || u.username,
              role: u.designation || u.role || "Employee",
              username: u.username,
              status: "offboard" as const,
              profilePicture: u.profilePicture,
            };
          });

        console.log("=== RESULTS ===");
        console.log("Onboarding employees:", onboarding.length, onboarding);
        console.log("Offboarding employees:", offboarding.length, offboarding);

        // Debug: Check what statuses we actually have
        console.log(
          "All statuses in filtered employees:",
          filtered.map((u: any) => ({
            username: u.username,
            status: u.status,
            statusType: typeof u.status,
          }))
        );

        setOnboardingEmployees(onboarding);
        setOffboardingEmployees(offboarding);
        setLoading(false);
        console.log(
          "✅ Final state - Onboarding:",
          onboarding.length,
          "Offboarding:",
          offboarding.length
        );
      } catch (error) {
        console.error("❌ ERROR in fetchEmployees:", error);
        console.error(
          "Error details:",
          error instanceof Error ? error.message : String(error)
        );
        console.error(
          "Error stack:",
          error instanceof Error ? error.stack : "No stack"
        );
        setLoading(false);
      }
    };

    // Only fetch if we have user and token
    if (user && token) {
      console.log("🔍 Calling fetchEmployees...");
      fetchEmployees().catch((error) => {
        console.error("❌ Unhandled error in fetchEmployees:", error);
      });
    } else {
      console.log("⏸️ Skipping fetchEmployees - missing user or token", {
        user: !!user,
        token: !!token,
      });
      setLoading(false);
    }
  }, [user, token]);

  // Fetch progress data when employee is selected
  useEffect(() => {
    if (!selectedEmployee || !token) {
      setEmployeeProgress(null);
      return;
    }

    const fetchEmployeeProgress = async () => {
      try {
        const isOnboarding = selectedEmployee.status === "onboard";
        const employeeId = selectedEmployee.employeeId;

        // Fetch onboarding progress if onboarding
        let qnaScore = 0;
        let qnaTotalQuestions = 0;

        if (isOnboarding) {
          try {
            const progressResponse = await fetch(
              `${API_URL}/api/onboarding/tasks?employeeId=${employeeId}`,
              {
                headers: { Authorization: `Bearer ${token}` },
              }
            );

            if (progressResponse.ok) {
              const progressData = await progressResponse.json();

              // Calculate QnA score
              const qaModules = progressData.onboarding?.qa?.modules || [];
              if (qaModules.length > 0) {
                let totalScore = 0;
                let totalQuestions = 0;

                qaModules.forEach((module: any) => {
                  if (module.score !== null && module.totalQuestions) {
                    totalScore += module.score;
                    totalQuestions += module.totalQuestions;
                  }
                });

                qnaScore =
                  totalQuestions > 0
                    ? Math.round((totalScore / totalQuestions) * 100)
                    : 0;
                qnaTotalQuestions = totalQuestions;
              }
            }
          } catch (error) {
            console.error("Error fetching onboarding progress:", error);
          }
        }

        // Generate progress data
        const sections = isOnboarding
          ? ["Overview", "Q&A", "Practice", "Bug Fixing"]
          : ["Final Call", "Handover", "Documentation"];

        const dummySections: SectionProgress[] = sections.map(
          (section, idx) => {
            const expected = [5, 4, 3.5, 5.5][idx] || 4;
            const spent =
              idx === 0
                ? 4.3
                : idx === 1
                ? 3.2
                : idx === 2
                ? 2.8
                : idx === 3
                ? 4.1
                : 0;
            const completion = spent ? Math.round((spent / expected) * 100) : 0;
            const status =
              idx < 2 ? "Pending" : idx === 3 ? "Pending" : "Completed";

            return {
              section,
              status: status as "Pending" | "Completed",
              expectedHours: expected,
              spentHours: spent,
              completion: completion > 100 ? 149 : completion,
              value: spent ? Math.round(spent * 10) : undefined,
            };
          }
        );

        const completed = dummySections.filter(
          (s) => s.status === "Completed"
        ).length;
        const pending = dummySections.filter(
          (s) => s.status === "Pending"
        ).length;
        const overallProgress = Math.round((completed / sections.length) * 100);
        const efficiency = Math.round(85 + Math.random() * 10);

        const timeSpentData = dummySections
          .filter((s) => s.spentHours !== null)
          .map((s) => ({
            section: s.section,
            expected: s.expectedHours,
            spent: s.spentHours || 0,
          }));

        // Generate time to productivity data (dummy for now, should come from backend)
        const timeToProductivity = Array.from({ length: 30 }, (_, i) => ({
          day: i + 1,
          productivity: Math.min(
            100,
            Math.round(20 + i * 2.5 + Math.random() * 10)
          ),
        }));

        setEmployeeProgress({
          employeeId: selectedEmployee.employeeId,
          employeeName: selectedEmployee.name,
          employeeRole: selectedEmployee.role,
          type: isOnboarding ? "onboarding" : "offboarding",
          pendingSections: pending,
          completedSections: completed,
          efficiency,
          overallProgress,
          sections: dummySections,
          timeSpentData,
          qnaScore,
          qnaTotalQuestions,
          activeRepos: selectedEmployee.active_repos || [],
          timeToProductivity,
        });
      } catch (error) {
        console.error("Error fetching employee progress:", error);
      }
    };

    fetchEmployeeProgress();
  }, [selectedEmployee, token]);

  // Filter employees based on search
  const filteredOnboarding = useMemo(() => {
    if (!searchQuery) return onboardingEmployees;
    const query = searchQuery.toLowerCase();
    return onboardingEmployees.filter(
      (emp) =>
        emp.name.toLowerCase().includes(query) ||
        emp.role.toLowerCase().includes(query) ||
        emp.username.toLowerCase().includes(query)
    );
  }, [onboardingEmployees, searchQuery]);

  const filteredOffboarding = useMemo(() => {
    if (!searchQuery) return offboardingEmployees;
    const query = searchQuery.toLowerCase();
    return offboardingEmployees.filter(
      (emp) =>
        emp.name.toLowerCase().includes(query) ||
        emp.role.toLowerCase().includes(query) ||
        emp.username.toLowerCase().includes(query)
    );
  }, [offboardingEmployees, searchQuery]);

  // Chart colors
  const COLORS = {
    pending: "#fb923c",
    completed: "#34d399",
    efficiency: "#a78bfa",
    donut: {
      pending: "#e2e8f0", // lighter slate for pending background
      completed: "#0E1B2E", // Navy for completed
    },
    grid: "#e5e7eb", // slightly darker grid for visibility on white
    text: "#64748b",
  };

  if (loading) {
    return (
      <Loader darkMode={false} message="Loading dashboard..." fullScreen />
    );
  }

  // Donut chart data
  const donutData = employeeProgress
    ? [
        {
          name: "Pending",
          value: 100 - employeeProgress.overallProgress,
          fill: COLORS.donut.pending,
        },
        {
          name: "Completed",
          value: employeeProgress.overallProgress,
          fill: COLORS.donut.completed,
        },
      ]
    : [];

  return (
    <div className={`min-h-screen flex bg-slate-50 ${inter.className}`}>
      {/* ================= SIDEBAR ================= */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col h-screen z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)]">
        {/* Sidebar Header */}
        <div className="px-6 py-6 border-b border-slate-100/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#0E1B2E] rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
              <img src="/logo.png" alt="Smarix Logo" className="w-6 h-6" />
            </div>
            <div>
              <h2 className={`${inter.className} text-xl font-bold tracking-tight text-[#0E1B2E]`}>
                Smarix
              </h2>
              <p className={`${inter.className} text-[10px] text-slate-400 font-semibold tracking-wider uppercase`}>
                Manager Dashboard
              </p>
            </div>
          </div>
        </div>

        {/* User Profile Card */}
        <div className="px-4 pt-6 pb-2">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between group hover:border-slate-200 transition-colors">
            {user && (
              <>
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className={`${inter.className} w-10 h-10 rounded-full bg-[#0E1B2E] text-white flex items-center justify-center font-bold text-sm shadow-sm shrink-0`}>
                    {user.name ? user.name.charAt(0).toUpperCase() : "M"}
                  </div>
                  <div className="min-w-0">
                    <div className={`${inter.className} text-sm font-bold text-slate-900 truncate`}>
                      {user.name || user.username}
                    </div>
                    <div className={`${inter.className} text-[11px] text-slate-500 capitalize font-medium truncate`}>
                      {user.role || "Manager"}
                    </div>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-white rounded-lg transition-all"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="px-4 py-4">
          <div className="relative group">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-[#0E1B2E] transition-colors" />
            <input
              type="text"
              placeholder="Search employees..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`${inter.className} w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E]/30 transition-all text-sm font-medium`}
            />
          </div>
        </div>

        {/* Lists */}
        <div className="flex-1 overflow-y-auto px-4 space-y-4 pb-6 scrollbar-hide">
          {/* Onboarding */}
          <div>
            <button
              onClick={() => setOnboardingExpanded(!onboardingExpanded)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider hover:text-slate-700 transition-colors mb-2 px-1"
            >
              <span className={`${inter.className}`}>Onboarding ({filteredOnboarding.length})</span>
              {onboardingExpanded ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>

            {onboardingExpanded && (
              <div className="space-y-1">
                {filteredOnboarding.length === 0 ? (
                  <div className={`${inter.className} py-4 text-center text-xs text-slate-400 italic bg-slate-50/50 rounded-lg border border-dashed border-slate-200`}>
                    No active onboarding
                  </div>
                ) : (
                  filteredOnboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`group p-2.5 flex items-center gap-3 cursor-pointer rounded-xl transition-all border ${
                        selectedEmployee?.id === emp.id
                          ? "bg-blue-50/80 border-blue-100 shadow-sm"
                          : "border-transparent hover:bg-slate-50 hover:border-slate-100"
                      }`}
                    >
                      <div className="relative">
                        <div
                          className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ring-2 ring-white ${
                            selectedEmployee?.id === emp.id
                              ? "bg-blue-600 text-white"
                              : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
                          }`}
                        >
                          {emp.profilePicture ? (
                            <img
                              src={emp.profilePicture}
                              alt={emp.name}
                              className="w-full h-full rounded-full object-cover"
                            />
                          ) : (
                            emp.name.charAt(0).toUpperCase()
                          )}
                        </div>
                        {selectedEmployee?.id === emp.id && (
                          <span className="absolute -right-0.5 -bottom-0.5 w-3 h-3 bg-blue-500 border-2 border-white rounded-full"></span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div
                          className={`
                           ${inter.className} text-sm font-semibold truncate ${
                            selectedEmployee?.id === emp.id
                              ? "text-blue-900"
                              : "text-slate-700 group-hover:text-slate-900"
                          }`}
                        >
                          {emp.name}
                        </div>
                        <div className={`${inter.className} text-[11px] truncate text-slate-500 font-medium`}>
                          {emp.role}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Offboarding */}
          <div>
            <button
              onClick={() => setOffboardingExpanded(!offboardingExpanded)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider hover:text-slate-700 transition-colors mb-2 px-1"
            >
              <span className={`${inter.className}`}>Offboarding ({filteredOffboarding.length})</span>
              {offboardingExpanded ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>

            {offboardingExpanded && (
              <div className="space-y-1">
                {filteredOffboarding.length === 0 ? (
                  <div className={`${inter.className} py-4 text-center text-xs text-slate-400 italic bg-slate-50/50 rounded-lg border border-dashed border-slate-200`}>
                    No active offboarding
                  </div>
                ) : (
                  filteredOffboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`group p-2.5 flex items-center gap-3 cursor-pointer rounded-xl transition-all border ${
                        selectedEmployee?.id === emp.id
                          ? "bg-amber-50/80 border-amber-100 shadow-sm"
                          : "border-transparent hover:bg-slate-50 hover:border-slate-100"
                      }`}
                    >
                      <div className="relative">
                        <div
                          className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ring-2 ring-white ${
                            selectedEmployee?.id === emp.id
                              ? "bg-amber-500 text-white"
                              : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
                          }`}
                        >
                          {emp.profilePicture ? (
                            <img
                              src={emp.profilePicture}
                              alt={emp.name}
                              className="w-full h-full rounded-full object-cover"
                            />
                          ) : (
                            emp.name.charAt(0).toUpperCase()
                          )}
                        </div>
                        {selectedEmployee?.id === emp.id && (
                          <span className="absolute -right-0.5 -bottom-0.5 w-3 h-3 bg-amber-500 border-2 border-white rounded-full"></span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div
                          className={`${inter.className} text-sm font-semibold truncate ${
                            selectedEmployee?.id === emp.id
                              ? "text-amber-900"
                              : "text-slate-700 group-hover:text-slate-900"
                          }`}
                        >
                          {emp.name}
                        </div>
                        <div className={`${inter.className} text-[11px] truncate text-slate-500 font-medium`}>
                          {emp.role}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ================= MAIN CONTENT ================= */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
        <div className="flex-1 overflow-y-auto p-8 lg:p-10">
          {!selectedEmployee ? (
            <div
              className="h-full flex flex-col items-center justify-center text-center opacity-0 animate-fadeIn"
              style={{ animationFillMode: "forwards" }}
            >
              <div className="relative group cursor-default">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative w-24 h-24 bg-white rounded-3xl shadow-xl flex items-center justify-center mb-6 border border-slate-100">
                  <Users className="w-10 h-10 text-slate-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </div>
              <h3 className={`${inter.className} text-2xl font-bold text-[#0E1B2E]`}>
                Welcome Back, {user?.name?.split(" ")[0] || "Manager"}
              </h3>
              <p className={`${inter.className} text-slate-500 mt-3 max-w-sm leading-relaxed text-sm`}>
                Select an employee from the sidebar to track their progress,
                manage tasks, or oversee handovers.
              </p>
            </div>
          ) : employeeProgress ? (
            <div className="space-y-8 max-w-[1600px] mx-auto animate-slideIn">
              {/* Header Card */}
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col xl:flex-row xl:items-center justify-between gap-6 relative overflow-hidden">
                {/* Decorative background accent */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-50/50 to-transparent rounded-bl-full pointer-events-none -z-0" />

                <div className="flex items-center gap-6 relative z-10">
                  <div className="relative">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#0E1B2E] to-blue-900 flex items-center justify-center text-white text-3xl font-bold shadow-xl shadow-blue-900/20 ring-4 ring-white">
                      {selectedEmployee.profilePicture ? (
                        <img
                          src={selectedEmployee.profilePicture}
                          className="w-full h-full rounded-2xl object-cover"
                        />
                      ) : (
                        selectedEmployee.name.charAt(0)
                      )}
                    </div>
                    <div
                      className={`absolute -bottom-2 -right-2 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider text-white shadow-md border-2 border-white ${
                        employeeProgress.type === "onboarding"
                          ? "bg-blue-500"
                          : "bg-amber-500"
                      }`}
                    >
                      {employeeProgress.type === "onboarding" ? "On" : "Off"}
                    </div>
                  </div>

                  <div>
                    <h1 className={`${inter.className} text-3xl font-bold text-[#0E1B2E] tracking-tight`}>
                      {employeeProgress.employeeName}
                    </h1>
                    <div className="flex flex-wrap items-center gap-3 mt-2">
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 text-xs font-semibold border border-slate-200">
                        <User className="w-3 h-3" />
                        {employeeProgress.employeeRole}
                      </div>
                      <span className="text-slate-300">|</span>
                      <div className={`${inter.className} text-sm text-slate-500 font-mono`}>
                        ID: {selectedEmployee.employeeId}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-4 relative z-10">
                  {/* Repo Chips */}
                  {employeeProgress.type === "onboarding" &&
                    employeeProgress.activeRepos &&
                    employeeProgress.activeRepos.length > 0 && (
                      <div className="flex items-center gap-2">
                        {employeeProgress.activeRepos.map((repo, idx) => (
                          <span
                            key={idx}
                            className={`${inter.className} px-3 py-1.5 rounded-full bg-white text-slate-600 border border-slate-200 text-xs font-mono font-medium shadow-sm`}
                          >
                            {repo}
                          </span>
                        ))}
                      </div>
                    )}

                  {employeeProgress.type === "offboarding" && (
                    <button
                      onClick={() =>
                        setManageOffboardingMode(!manageOffboardingMode)
                      }
                      className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all shadow-sm ${
                        manageOffboardingMode
                          ? "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                          : "bg-[#0E1B2E] text-white hover:bg-blue-900 hover:shadow-lg hover:shadow-blue-900/20 active:scale-95"
                      }`}
                    >
                      <Settings className="w-4 h-4" />
                      <span className={`${inter.className}`}>
                        {manageOffboardingMode
                          ? "View Analytics"
                          : "Manage Offboarding"}
                      </span>
                    </button>
                  )}
                  {/* <button className="p-3 rounded-xl border border-slate-200 text-slate-400 hover:text-[#0E1B2E] hover:border-slate-300 hover:bg-white transition-all bg-white shadow-sm">
                    <MoreVertical className="w-5 h-5" />
                  </button> */}
                </div>
              </div>

              {manageOffboardingMode &&
              employeeProgress.type === "offboarding" ? (
                <div className="space-y-6 animate-fadeIn">
                  {/* Section Tabs */}
                  <div className="inline-flex p-1.5 bg-white rounded-xl border border-slate-200 shadow-sm">
                    {(["finalcall", "handover", "documentation"] as const).map(
                      (section) => (
                        <button
                          key={section}
                          onClick={() => setActiveOffboardingSection(section)}
                          className={` ${inter.className} px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${
                            activeOffboardingSection === section
                              ? "bg-[#0E1B2E] text-white shadow-md"
                              : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
                          }`}
                        >
                          {section === "finalcall"
                            ? "Final Call"
                            : section.charAt(0).toUpperCase() +
                              section.slice(1)}
                        </button>
                      )
                    )}
                  </div>

                  {/* Section Content */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden min-h-[600px] p-2">
                    {activeOffboardingSection === "finalcall" && (
                      <FinalCallSection
                        employeeId={
                          selectedEmployee.employeeId ||
                          selectedEmployee.id ||
                          ""
                        }
                        darkMode={false}
                      />
                    )}
                    {activeOffboardingSection === "handover" && (
                      <HandoverSection
                        employeeId={
                          selectedEmployee.employeeId ||
                          selectedEmployee.id ||
                          ""
                        }
                        darkMode={false}
                      />
                    )}
                    {activeOffboardingSection === "documentation" && (
                      <DocumentationSection
                        employeeId={
                          selectedEmployee.employeeId ||
                          selectedEmployee.id ||
                          ""
                        }
                        darkMode={false}
                      />
                    )}
                  </div>
                </div>
              ) : (
                <div className="animate-fadeIn space-y-8">
                  {/* KPI Cards */}
                  <div
                    className={`grid ${
                      employeeProgress.type === "onboarding"
                        ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
                        : "grid-cols-1 md:grid-cols-3"
                    } gap-5`}
                  >
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow group">
                      <div className="flex items-center justify-between mb-4">
                        <span className={`${inter.className} text-xs font-bold text-slate-400 uppercase tracking-wider`}>
                          Pending Tasks
                        </span>
                        <div className="p-2 rounded-lg bg-orange-50 text-orange-600 border border-orange-100 group-hover:scale-110 transition-transform">
                          <Clock className="w-5 h-5" />
                        </div>
                      </div>
                      <div className="flex items-end gap-2">
                        <div className={`${inter.className} text-4xl font-bold text-slate-800 tracking-tight`}>
                          {employeeProgress.pendingSections}
                        </div>
                        <div className={`${inter.className} text-sm font-medium text-slate-500 mb-1`}>
                          Sections
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow group">
                      <div className="flex items-center justify-between mb-4">
                        <span className={`${inter.className} text-xs font-bold text-slate-400 uppercase tracking-wider`}>
                          Completed
                        </span>
                        <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100 group-hover:scale-110 transition-transform">
                          <CheckCircle className="w-5 h-5" />
                        </div>
                      </div>
                      <div className="flex items-end gap-2">
                        <div className={`${inter.className} text-4xl font-bold text-slate-800 tracking-tight`}>
                          {employeeProgress.completedSections}
                        </div>
                        <div className={`${inter.className} text-sm font-medium text-slate-500 mb-1`}>
                          Sections
                        </div>
                      </div>
                    </div>

                    {employeeProgress.type === "onboarding" &&
                      employeeProgress.qnaScore !== undefined && (
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow group">
                          <div className="flex items-center justify-between mb-4">
                            <span className={`${inter.className} text-xs font-bold text-slate-400 uppercase tracking-wider`}>
                              Quiz Score
                            </span>
                            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 group-hover:scale-110 transition-transform">
                              <TrendingUp className="w-5 h-5" />
                            </div>
                          </div>
                          <div className="flex items-end gap-2">
                            <div className={`${inter.className} text-4xl font-bold text-slate-800 tracking-tight`}>
                              {employeeProgress.qnaScore}%
                            </div>
                            <div className={`${inter.className} text-sm font-medium text-slate-500 mb-1`}>
                              Average
                            </div>
                          </div>
                        </div>
                      )}

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow group">
                      <div className="flex items-center justify-between mb-4">
                        <span className={`${inter.className} text-xs font-bold text-slate-400 uppercase tracking-wider`}>
                          Efficiency
                        </span>
                        <div className="p-2 rounded-lg bg-purple-50 text-purple-600 border border-purple-100 group-hover:scale-110 transition-transform">
                          <Activity className="w-5 h-5" />
                        </div>
                      </div>
                      <div className="flex items-end gap-2">
                        <div className={`${inter.className} text-4xl font-bold text-slate-800 tracking-tight`}>
                          {employeeProgress.efficiency}%
                        </div>
                        <div className={`${inter.className} text-sm font-medium text-slate-500 mb-1`}>
                          Calculated
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Charts Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Area Chart: Time to Productivity */}
                    {employeeProgress.timeToProductivity && (
                      <div className="lg:col-span-2 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                        <div className="mb-8">
                          <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}>
                            Productivity Ramp-up
                          </h3>
                          <p className={`${inter.className} text-sm text-slate-500`}>
                            Estimated contribution level over the first 30 days
                          </p>
                        </div>
                        <div className="h-[300px] w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart
                              data={employeeProgress.timeToProductivity}
                              margin={{
                                top: 10,
                                right: 10,
                                left: 0,
                                bottom: 0,
                              }}
                            >
                              <defs>
                                <linearGradient
                                  id="colorProd"
                                  x1="0"
                                  y1="0"
                                  x2="0"
                                  y2="1"
                                >
                                  <stop
                                    offset="5%"
                                    stopColor="#3b82f6"
                                    stopOpacity={0.2}
                                  />
                                  <stop
                                    offset="95%"
                                    stopColor="#3b82f6"
                                    stopOpacity={0}
                                  />
                                </linearGradient>
                              </defs>
                              <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={false}
                                stroke={COLORS.grid}
                              />
                              <XAxis
                                dataKey="day"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: COLORS.text, fontSize: 12 }}
                                dy={10}
                                tickFormatter={(val) => `D${val}`}
                              />
                              <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: COLORS.text, fontSize: 12 }}
                                domain={[0, 100]}
                                unit="%"
                              />
                              <Tooltip content={<CustomTooltip />} />
                              <Area
                                type="monotone"
                                dataKey="productivity"
                                stroke="#3b82f6"
                                strokeWidth={3}
                                fillOpacity={1}
                                fill="url(#colorProd)"
                                name="Productivity"
                                unit="%"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}

                    {/* Donut Chart: Overall Status */}
                    <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div>
                        <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E] mb-1`}>
                          Overall Status
                        </h3>
                        <p className={`${inter.className} text-sm text-slate-500`}>
                          Completion breakdown
                        </p>
                      </div>

                      <div className="flex-1 flex items-center justify-center relative py-6">
                        <ResponsiveContainer width="100%" height={250}>
                          <PieChart>
                            <Pie
                              data={donutData}
                              cx="50%"
                              cy="50%"
                              innerRadius={70}
                              outerRadius={90}
                              paddingAngle={0}
                              dataKey="value"
                              stroke="none"
                            >
                              {donutData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                              ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                          </PieChart>
                        </ResponsiveContainer>
                        {/* Centered Text */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                          <span className={`${inter.className} text-4xl font-bold text-[#0E1B2E] tracking-tight`}>
                            {employeeProgress.overallProgress}%
                          </span>
                          <span className={`${inter.className} text-xs text-slate-400 font-bold uppercase tracking-wider mt-1`}>
                            Done
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                          <div
                            className="w-2 h-8 rounded-full"
                            style={{ backgroundColor: COLORS.donut.pending }}
                          />
                          <div>
                            <div className={`${inter.className} text-[10px] text-slate-500 font-bold uppercase tracking-wider`}>
                              Pending
                            </div>
                            <div className={`${inter.className} text-lg font-bold text-slate-700`}>
                              {100 - employeeProgress.overallProgress}%
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                          <div
                            className="w-2 h-8 rounded-full"
                            style={{ backgroundColor: COLORS.donut.completed }}
                          />
                          <div>
                            <div className={`${inter.className} text-[10px] text-slate-500 font-bold uppercase tracking-wider`}>
                              Done
                            </div>
                            <div className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}>
                              {employeeProgress.overallProgress}%
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Bar Chart: Time Spent */}
                    <div className="lg:col-span-3 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
                        <div>
                          <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}>
                            Time Allocation
                          </h3>
                          <p className={`${inter.className} text-sm text-slate-500`}>
                            Expected vs Actual hours per module
                          </p>
                        </div>
                        <div className="flex gap-6">
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-slate-200 ring-2 ring-slate-50"></span>
                            <span className={`${inter.className} text-xs font-bold text-slate-600 uppercase tracking-wide`}>
                              Expected
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-emerald-50"></span>
                            <span className={`${inter.className} text-xs font-bold text-slate-600 uppercase tracking-wide`}>
                              Actual
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <ComposedChart
                            data={employeeProgress.timeSpentData}
                            barGap={0}
                            barSize={48}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                              vertical={false}
                              stroke={COLORS.grid}
                            />
                            <XAxis
                              dataKey="section"
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: COLORS.text, fontSize: 13, fontFamily: inter.style.fontFamily }}
                              dy={15}
                            />
                            <YAxis
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: COLORS.text, fontSize: 12, fontFamily: inter.style.fontFamily }}
                              label={{
                                value: "Hours",
                                angle: -90,
                                position: "insideLeft",
                                style: { fill: COLORS.text, fontSize: 12, fontFamily: inter.style.fontFamily},
                              }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar
                              dataKey="expected"
                              fill="#e2e8f0"
                              radius={[6, 6, 0, 0]}
                              name="Expected"
                              unit="h"
                            />
                            <Bar
                              dataKey="spent"
                              fill="#10b981"
                              radius={[6, 6, 0, 0]}
                              name="Spent"
                              unit="h"
                            />
                          </ComposedChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Table Section */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                      <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E]`}>
                        Module Details
                      </h3>
                      {/* <button className={`${inter.className} text-sm text-blue-600 font-bold hover:text-blue-700 transition-colors`}>
                        View Full Report
                      </button> */}
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-50/80 border-b border-slate-100">
                            <th className={`${inter.className} py-4 px-6 text-xs font-bold uppercase tracking-wider text-slate-500`}>
                              Section
                            </th>
                            <th className={`${inter.className} py-4 px-6 text-xs font-bold uppercase tracking-wider text-slate-500`}>
                              Status
                            </th>
                            <th className={`${inter.className} py-4 px-6 text-xs font-bold uppercase tracking-wider text-slate-500`}>
                              Hours (Exp / Act)
                            </th>
                            <th className={`${inter.className} py-4 px-6 text-xs font-bold uppercase tracking-wider text-slate-500 w-1/3`}>
                              Progress
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {employeeProgress.sections.map((section, idx) => (
                            <tr
                              key={idx}
                              className="hover:bg-slate-50/80 transition-colors group"
                            >
                              <td className={`${inter.className} py-5 px-6 font-semibold text-slate-700 group-hover:text-[#0E1B2E] transition-colors`}>
                                {section.section}
                              </td>
                              <td className="py-5 px-6">
                                <span
                                  className={`$ inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold shadow-sm border ${
                                    inter.className
                                  } inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold shadow-sm border ${
                                    section.status === "Completed"
                                      ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                                      : "bg-amber-50 text-amber-700 border-amber-100"
                                  }`}
                                >
                                  {section.status === "Completed" ? (
                                    <CheckCircle className="w-3.5 h-3.5" />
                                  ) : (
                                    <Clock className="w-3.5 h-3.5" />
                                  )}
                                  {section.status}
                                </span>
                              </td>
                              <td className={`${inter.className} py-5 px-6 text-sm text-slate-600 font-mono`}>
                                <span className={`${inter.className} text-slate-400`}>
                                  {section.expectedHours}h
                                </span>
                                <span className="mx-2 text-slate-200">/</span>
                                <span
                                  className={`${inter.className} font-bold ${
                                    section.spentHours &&
                                    section.spentHours > section.expectedHours
                                      ? "text-amber-600"
                                      : "text-slate-800"
                                  }`}
                                >
                                  {section.spentHours ?? "-"}h
                                </span>
                              </td>
                              <td className="py-5 px-6">
                                <div className="flex items-center gap-4">
                                  <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden shadow-inner">
                                    <div
                                      className={`h-full rounded-full transition-all duration-1000 ease-out ${
                                        section.completion >= 100
                                          ? "bg-emerald-500"
                                          : "bg-blue-500"
                                      }`}
                                      style={{
                                        width: `${Math.min(
                                          section.completion,
                                          100
                                        )}%`,
                                      }}
                                    />
                                  </div>
                                  <span className="text-xs font-bold text-slate-700 w-10 text-right">
                                    {section.completion}%
                                  </span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <Loader darkMode={false} message="Loading Data..." />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
