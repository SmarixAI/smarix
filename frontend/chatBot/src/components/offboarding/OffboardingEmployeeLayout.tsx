"use client";

import { useState, useEffect } from "react";
import { Briefcase, Moon, Sun, User, LogOut } from "lucide-react";
import Sidebar from "./Sidebar";
import EmployeeFinalCallSection from "./employeeViewSections/FinalCallSection";
import EmployeeHandoverSection from "./employeeViewSections/HandoverSection";
import EmployeeDocumentationSection from "./employeeViewSections/DocumentationSection";
import Loader from "./Loader";
import { useAuth } from "@/components/auth/AuthContext";
import Chatbot from "@/components/onboarding/Chatbot";

const API_URL = "http://localhost:8000";

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

type OffboardingEmployeeLayoutProps = {
  darkMode?: boolean;
  setDarkMode?: (value: boolean) => void;
};

export default function OffboardingEmployeeLayout({
  darkMode = false,
  setDarkMode,
}: OffboardingEmployeeLayoutProps = {}) {
  const { user, logout, token } = useAuth();
  const [activeSection, setActiveSection] = useState<SectionType>("finalcall");
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

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

  if (loading) {
    return (
      <Loader
        darkMode={darkMode}
        message="Loading your offboarding data..."
        fullScreen
      />
    );
  }

  if (!employee) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div
          className={`text-center p-8 rounded-xl border ${
            darkMode
              ? "border-gray-700 bg-gray-800"
              : "border-slate-200 bg-white"
          }`}
        >
          <p
            className={`text-lg font-semibold ${
              darkMode ? "text-gray-300" : "text-slate-700"
            }`}
          >
            Unable to load profile data.
          </p>
          <button
            onClick={logout}
            className="mt-4 text-indigo-500 hover:underline"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-0">
      <header
        className={`border-b shadow-sm transition-colors duration-300 ${
          darkMode
            ? "glass-card-dark border-gray-700"
            : "glass-card-light border-slate-200"
        }`}
      >
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center gap-6">
          <div className="flex-1 flex items-start gap-3">
            <div className="mt-1 p-2 rounded-xl bg-indigo-200 text-indigo-700">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h1
                className={`text-2xl font-extrabold tracking-tight ${
                  darkMode ? "text-gray-100" : "text-slate-900"
                }`}
              >
                Offboarding – Employee View
              </h1>
              <p
                className={`text-sm font-medium ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}
              >
                Track your tasks, handovers, and documentation
              </p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            {setDarkMode && (
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg transition ${
                  darkMode
                    ? "hover:bg-gray-800 text-yellow-400"
                    : "hover:bg-indigo-50 text-indigo-600"
                }`}
              >
                {darkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
            )}
            {user && (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className={`p-2 rounded-full transition ${
                    darkMode
                      ? "hover:bg-gray-800 text-gray-300"
                      : "hover:bg-indigo-50 text-slate-700"
                  }`}
                >
                  <User className="w-5 h-5" />
                </button>
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <div
                      className={`absolute right-0 mt-2 w-52 rounded-xl border shadow-xl z-20 ${
                        darkMode
                          ? "glass-card-dark border-gray-700"
                          : "glass-card-light border-slate-200"
                      }`}
                    >
                      <div className="px-4 py-3 border-b dark:border-gray-700">
                        <p
                          className={`text-sm font-medium ${
                            darkMode ? "text-white" : "text-slate-900"
                          }`}
                        >
                          {employee.name}
                        </p>
                        <p
                          className={`text-xs ${
                            darkMode ? "text-gray-400" : "text-slate-500"
                          }`}
                        >
                          {employee.role}
                        </p>
                      </div>
                      <div className="p-2 space-y-1">
                        <button
                          onClick={() => {
                            logout();
                            setUserMenuOpen(false);
                          }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                            darkMode
                              ? "hover:bg-gray-800 text-gray-300"
                              : "hover:bg-indigo-50 text-slate-700"
                          }`}
                        >
                          <LogOut className="w-4 h-4" /> Logout
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="p-6 max-w-screen-2xl mx-auto">
        <div className="grid grid-cols-12 gap-6">
          <aside className="col-span-3 space-y-6">
            <Sidebar
              activeSection={activeSection}
              onChangeSection={setActiveSection}
              selectedEmployee={employee}
              darkMode={darkMode}
            />
          </aside>
          <main className="col-span-9 space-y-6">
            <div
              className={`border rounded-2xl shadow-sm p-2 transition-colors duration-300 ${
                darkMode
                  ? "glass-card-dark border-gray-700"
                  : "glass-card-light border-slate-200"
              }`}
            >
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: "finalcall", label: "Final Call" },
                  { key: "handover", label: "Handover" },
                  { key: "documentation", label: "Documentation" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveSection(tab.key as SectionType)}
                    className={`py-3 rounded-xl text-sm font-semibold transition ${
                      activeSection === tab.key
                        ? darkMode
                          ? "bg-indigo-600 text-white shadow"
                          : "bg-indigo-700 text-white shadow"
                        : darkMode
                        ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                        : "bg-slate-100 text-slate-900 hover:bg-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            <div
              className={`rounded-2xl shadow border p-6 transition-colors duration-300 ${
                darkMode
                  ? "glass-card-dark border-gray-700"
                  : "glass-card-light border-slate-200"
              }`}
            >
              {activeSection === "finalcall" && employee.employeeId && (
                <EmployeeFinalCallSection
                  employeeId={employee.employeeId}
                  darkMode={darkMode}
                />
              )}
              {activeSection === "handover" && employee.employeeId && (
                <EmployeeHandoverSection
                  employeeId={employee.employeeId}
                  darkMode={darkMode}
                />
              )}
              {activeSection === "documentation" && employee.employeeId && (
                <EmployeeDocumentationSection
                  employeeId={employee.employeeId}
                  darkMode={darkMode}
                />
              )}
            </div>
          </main>
        </div>
      </div>
      <Chatbot darkMode={darkMode} role="offboarding" />
    </div>
  );
}
