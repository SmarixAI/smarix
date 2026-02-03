"use client";

import { useState, useEffect } from "react";
import {
  Phone,
  RefreshCw,
  FileText,
  ArrowLeft,
  Calendar,
  AlertCircle,
  LogOut,
  Bot,
} from "lucide-react";
import Image from "next/image";
import Sidebar from "./Sidebar";
import EmployeeFinalCallSection from "./employeeViewSections/FinalCallSection";
import EmployeeHandoverSection from "./employeeViewSections/HandoverSection";
import EmployeeDocumentationSection from "./employeeViewSections/DocumentationSection";
import Loader from "./Loader";
import { useAuth } from "@/components/auth/AuthContext";
import Chatbot from "@/components/onboarding/Chatbot";
import { Inter, JetBrains_Mono } from "next/font/google";
import { useRouter } from "next/navigation";

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

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export default function OffboardingEmployeeLayout({}: OffboardingEmployeeLayoutProps = {}) {
  const { user, logout, token } = useAuth();
  const [activeSection, setActiveSection] = useState<SectionType>("finalcall");
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [effectiveWorkdays, setEffectiveWorkdays] = useState<number | null>(
    null
  );
  const [highRiskTasksPending, setHighRiskTasksPending] = useState<number>(0);

  const router = useRouter();

  const handleChatbot = () => {
    window.open("/chat", "_blank", "noopener,noreferrer");
  };

  useEffect(() => {
    const fetchEmployeeData = async () => {
      try {
        if (!user || !token) {
          return;
        }

        const response = await fetch(`${API_URL}/auth/users`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const users = await response.json();
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
              lastDay: currentUserData.last_day || null,
            });
          } else {
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
      console.error("Error calculating workdays:", error);
      setEffectiveWorkdays(null);
    }
  }, [employee?.lastDay]);

  useEffect(() => {
    if (!employee?.employeeId) {
      setHighRiskTasksPending(0);
      return;
    }

    const fetchTasks = async () => {
      try {
        const response = await fetch("/api/offboarding/tasks");
        if (!response.ok) {
          console.error("Failed to fetch tasks data");
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
            task.priority === "High" && task.status !== "not_needed"
        ).length;

        setHighRiskTasksPending(highRiskCount);
      } catch (error) {
        console.error("Error fetching tasks:", error);
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-white via-slate-50 to-blue-50/30">
        <div
          className={`${inter.className} text-center p-8 rounded-2xl border-2 border-slate-200 bg-white/70 backdrop-blur-sm shadow-lg max-w-md`}
        >
          <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-slate-400" />
          </div>
          <p className="text-lg font-semibold text-[#0E1B2E] mb-4">
            Unable to load profile data.
          </p>
          <button
            onClick={logout}
            className="px-6 py-2.5 rounded-xl font-semibold transition-all bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white hover:shadow-lg"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50/30 relative overflow-hidden">
      <div className="absolute inset-0 bg-white pointer-events-none" />

      <div className="h-screen relative flex">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(14,27,46,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(14,27,46,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

        <aside className="w-80 flex-shrink-0 border-r border-slate-200/60 bg-white/80 backdrop-blur-xl relative z-10 flex flex-col shadow-lg">
          <div className="p-5 border-b border-slate-200/60 bg-gradient-to-r from-white to-slate-50/50">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-gradient-to-br from-[#0E1B2E] to-blue-900 rounded-xl flex items-center justify-center overflow-hidden shadow-md shadow-slate-300/30 border border-slate-200/40">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={28}
                  height={28}
                  className="w-7 h-7 object-contain"
                />
              </div>
              <h2
                className={`${inter.className} text-xl font-bold tracking-tight text-[#0E1B2E]`}
              >
                Smarix
              </h2>
            </div>
            <p
              className={`${inter.className} text-sm text-slate-600 ml-[52px] font-medium`}
            >
              Offboarding Dashboard
            </p>
          </div>

          <div className="p-5 border-b border-slate-200/60">
            <div className="flex items-center justify-between mb-4">
              {employee && (
                <>
                  <div className="flex-1 min-w-0">
                    <div
                      className={`${inter.className} text-sm font-semibold text-[#0E1B2E] truncate`}
                    >
                      {employee.name}
                    </div>
                    <div
                      className={`${inter.className} text-xs text-slate-600 capitalize truncate font-medium`}
                    >
                      {employee.designation || employee.role}
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    className={`${inter.className} flex items-center gap-2 px-4 py-2.5 rounded-xl hover:bg-slate-50 transition-all border-2 border-slate-200 text-[#F54927] hover:border-slate-300 text-sm font-semibold shadow-sm hover:shadow-md`}
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </>
              )}
            </div>

            <div className="pb-2 mb-2">
              <button
                  onClick={handleChatbot}
                  className={`${inter.className} w-full flex items-center justify-center gap-3 px-3 py-5 rounded-xl bg-[#0E1B2E] hover:bg-[#0E1B2E]/20 hover:text-[#0E1B2E] transition-all border-2 border-blue-500 hover:border-[#0E1B2E] text-sm font-semibold shadow-sm hover:shadow-md`}
                  title="Chatbot "
                >
                  <Bot className="w-4 h-4" />
                  Go to Smarix Chatbot
                </button>
          </div>

            {employee && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-50/80 to-indigo-50/50 border-2 border-blue-200/60 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="w-3.5 h-3.5 text-blue-600" />
                    <p
                      className={`${inter.className} text-xs text-blue-900 font-semibold`}
                    >
                      Last Working Day
                    </p>
                  </div>
                  <p
                    className={`${jetbrainsMono.className} text-sm font-bold text-[#0E1B2E] ml-5.5`}
                  >
                    {employee.lastDay || "Not set"}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-gradient-to-br from-green-50/80 to-emerald-50/50 border-2 border-green-200/60 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="w-3.5 h-3.5 text-green-600" />
                    <p
                      className={`${inter.className} text-xs text-green-900 font-semibold`}
                    >
                      Effective Workdays
                    </p>
                  </div>
                  <p
                    className={`${jetbrainsMono.className} text-sm font-bold text-[#0E1B2E] ml-5.5`}
                  >
                    {effectiveWorkdays !== null
                      ? `${effectiveWorkdays} ${
                          effectiveWorkdays === 1 ? "Day" : "Days"
                        }`
                      : "N/A"}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-gradient-to-br from-red-50/80 to-orange-50/50 border-2 border-red-200/60 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle className="w-3.5 h-3.5 text-red-600" />
                    <p
                      className={`${inter.className} text-xs text-red-900 font-semibold`}
                    >
                      High-Risk Tasks
                    </p>
                  </div>
                  <p
                    className={`${jetbrainsMono.className} text-sm font-bold text-[#0E1B2E] ml-5.5`}
                  >
                    {highRiskTasksPending}{" "}
                    {highRiskTasksPending === 1 ? "Task" : "Tasks"}
                  </p>
                </div>
              </div>
            )}
          </div>

          <nav className="flex-1 overflow-y-auto">
            <div className="border-t border-slate-200/60 p-5">
              <div className="space-y-2">
                {[
                  { key: "finalcall", label: "Final Call", icon: Phone },
                  { key: "handover", label: "Handover", icon: RefreshCw },
                  {
                    key: "documentation",
                    label: "Documentation",
                    icon: FileText,
                  },
                ].map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setActiveSection(item.key as SectionType)}
                    className={`${
                      inter.className
                    } w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                      activeSection === item.key
                        ? "bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white shadow-lg"
                        : "text-[#0E1B2E] hover:bg-slate-50 border-2 border-transparent hover:border-slate-200"
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

        <main className="flex-1 relative z-10 flex flex-col overflow-hidden">
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

      <div className="fixed bottom-10 right-10 z-[100] transition-transform shadow-2xl rounded-full">
        <Chatbot role="offboarding" />
      </div>
    </div>
  );
}
