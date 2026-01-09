"use client";

import { useState, useEffect } from "react";
import { Phone, RefreshCw, FileText, LogOut } from "lucide-react";
import Image from "next/image";
import Sidebar from "./Sidebar";
import EmployeeFinalCallSection from "./employeeViewSections/FinalCallSection";
import EmployeeHandoverSection from "./employeeViewSections/HandoverSection";
import EmployeeDocumentationSection from "./employeeViewSections/DocumentationSection";
import Loader from "./Loader";
import { useAuth } from "@/components/auth/AuthContext";
import Chatbot from "@/components/onboarding/Chatbot";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type SectionType = "finalcall" | "handover" | "documentation";

type Employee = {
  id: string;
  employeeId?: string;
  name: string;
  role: string;
  designation?: string;
  risk: "high" | "medium" | "low";
  status: "active" | "leaving";
  lastDay: string | null;
};

type OffboardingEmployeeLayoutProps = {};

export default function OffboardingEmployeeLayout({}: OffboardingEmployeeLayoutProps = {}) {
  const { user, logout, token } = useAuth();
  const [activeSection, setActiveSection] = useState<SectionType>("finalcall");
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [effectiveWorkdays, setEffectiveWorkdays] = useState<number | null>(null);
  const [highRiskTasksPending, setHighRiskTasksPending] = useState<number>(0);

  useEffect(() => {
    const fetchEmployeeData = async () => {
      try {
        if (!user || !token) {
          // If no user/token yet, keep loading or just return
          return;
        }

        // Fetch latest data from DB to get 'lastDay' and real status
        const response = await fetch(`${API_URL}/auth/users`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const users = await response.json();
          // Find the current logged-in user in the list
          const currentUserData = users.find(
            (u: any) => u.username === user.username
          );

          if (currentUserData) {
            setEmployee({
              id: currentUserData.id,
              employeeId:
                currentUserData.employee_id ||
                currentUserData.employeeId ||
                "UNKNOWN",
              name: currentUserData.name || currentUserData.username,
              role: currentUserData.role || "Employee",
              designation: currentUserData.designation,
              risk: "medium",
              status:
                currentUserData.status === "offboard" ? "leaving" : "active",
              // Map DB snake_case to frontend camelCase
              lastDay: currentUserData.last_day || null,
            });
          } else {
            // Fallback if user not found in list (should rarely happen)
            setEmployee({
              id: user.employeeId || user.username,
              employeeId: user.employeeId || "UNKNOWN",
              name: user.name || user.username,
              role: user.role,
              designation: user.designation,
              risk: "medium",
              status: "active",
              lastDay: null,
            });
          }
        }
      } catch (error) {
        console.error("Error fetching employee data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployeeData();
  }, [user, token]);

  // Calculate effective workdays remaining
  useEffect(() => {
    if (!employee?.lastDay) {
      setEffectiveWorkdays(null);
      return;
    }

    try {
      const lastDay = new Date(employee.lastDay);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      lastDay.setHours(0, 0, 0, 0);

      const diffTime = lastDay.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays <= 0) {
        setEffectiveWorkdays(0);
        return;
      }

      const effectiveDays = Math.round(diffDays * 0.6);
      setEffectiveWorkdays(effectiveDays);
    } catch (error) {
      console.error('Error calculating workdays:', error);
      setEffectiveWorkdays(null);
    }
  }, [employee?.lastDay]);

  // Fetch and count high-risk tasks
  useEffect(() => {
    if (!employee?.employeeId) {
      setHighRiskTasksPending(0);
      return;
    }

    const fetchTasks = async () => {
      try {
        const response = await fetch('/api/offboarding/tasks');
        if (!response.ok) {
          console.error('Failed to fetch tasks data');
          return;
        }
        const data = await response.json();
        
        if (!data?.employees?.length) return;

        const foundEmployee = data.employees.find(
          (e: any) => e.employeeId === employee.employeeId
        );

        if (!foundEmployee) return;

        const aiTasks = foundEmployee.tasks?.ai ?? [];
        const managerTasks = foundEmployee.tasks?.manager ?? [];
        const allTasks = [...aiTasks, ...managerTasks];

        const highRiskCount = allTasks.filter(
          (task: any) => 
            task.priority === 'High' && 
            task.status !== 'not_needed'
        ).length;

        setHighRiskTasksPending(highRiskCount);
      } catch (error) {
        console.error('Error fetching tasks:', error);
      }
    };

    fetchTasks();
  }, [employee?.employeeId]);

  if (loading) {
    return (
      <Loader
        darkMode={false}
        message="Loading your offboarding data..."
        fullScreen
      />
    );
  }

  if (!employee) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
        <div className="text-center p-8 rounded-xl border border-gray-200 bg-white shadow-sm">
          <p className="text-lg font-semibold text-[#0E1B2E]">
            Unable to load profile data.
          </p>
          <button
            onClick={logout}
            className="mt-4 text-[#0E1B2E] hover:underline"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      <div className="h-screen relative flex">
        {/* Grid Pattern Background - matching landing page */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        {/* Sidebar with Navigation */}
        <aside className="w-80 flex-shrink-0 border-r border-gray-200 bg-white relative z-10 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={24}
                  height={24}
                  className="w-6 h-6 object-contain"
                />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-[#0E1B2E]">
                Smarix
              </h2>
            </div>
            <p className="text-sm text-[#0E1B2E]/60 ml-11">
              Offboarding Dashboard
            </p>
          </div>

          {/* Profile & Logout */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              {employee && (
                <>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-[#0E1B2E] truncate">
                      {employee.name}
                    </div>
                    <div className="text-xs text-[#0E1B2E]/60 capitalize truncate">
                      {employee.designation || employee.role}
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    className="ml-2 p-2 rounded-lg hover:bg-red-50 transition-colors text-red-600"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>

            {/* Employee Info */}
            {employee && (
              <div className="space-y-2">
                <div className="p-2.5 rounded-lg bg-[#0E1B2E]/5">
                  <p className="text-[10px] text-[#0E1B2E]/60 mb-0.5">
                    Last Working Day
                  </p>
                  <p className="text-xs font-semibold text-[#0E1B2E]">
                    {employee.lastDay || 'Not set'}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#0E1B2E]/5">
                  <p className="text-[10px] text-[#0E1B2E]/60 mb-0.5">
                    Effective Workdays
                  </p>
                  <p className="text-xs font-semibold text-[#0E1B2E]">
                    {effectiveWorkdays !== null 
                      ? `${effectiveWorkdays} ${effectiveWorkdays === 1 ? 'Day' : 'Days'}`
                      : 'N/A'}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#0E1B2E]/5">
                  <p className="text-[10px] text-[#0E1B2E]/60 mb-0.5">
                    High-Risk Tasks
                  </p>
                  <p className="text-xs font-semibold text-[#0E1B2E]">
                    {highRiskTasksPending} {highRiskTasksPending === 1 ? 'Task' : 'Tasks'}
                  </p>
                </div>
              </div>
            )}
          </div>

          <nav className="flex-1 overflow-y-auto">

            {/* Sections Navigation */}
            <div className="border-t border-gray-200 p-4">
              <div className="space-y-1">
                {[
                  { key: "finalcall", label: "Final Call", icon: Phone },
                  { key: "handover", label: "Handover", icon: RefreshCw },
                  { key: "documentation", label: "Documentation", icon: FileText },
                ].map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setActiveSection(item.key as SectionType)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${
                      activeSection === item.key
                        ? "bg-[#0E1B2E] text-white"
                        : "text-[#0E1B2E] hover:bg-[#0E1B2E]/5"
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 relative z-10 flex flex-col overflow-hidden">
          {/* Section Content */}
          {activeSection === "finalcall" && employee.employeeId && (
            <div className="flex-1 px-6 pb-6 flex flex-col overflow-hidden">
              <EmployeeFinalCallSection
                employeeId={employee.employeeId}
                darkMode={false}
              />
            </div>
          )}

          {activeSection === "handover" && employee.employeeId && (
            <div className="flex-1 px-6 pb-6 flex flex-col overflow-hidden">
              <EmployeeHandoverSection
                employeeId={employee.employeeId}
                darkMode={false}
              />
            </div>
          )}

          {activeSection === "documentation" && employee.employeeId && (
            <div className="flex-1 px-6 pb-6 flex flex-col overflow-hidden">
              <EmployeeDocumentationSection
                employeeId={employee.employeeId}
                darkMode={false}
              />
            </div>
          )}
        </main>
      </div>
      <Chatbot role="offboarding" />
    </div>
  );
}
