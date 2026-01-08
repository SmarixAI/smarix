"use client";

import { useState, useEffect } from "react";
import { Briefcase, User, LogOut } from "lucide-react";
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
        darkMode={false}
        message="Loading your offboarding data..."
        fullScreen
      />
    );
  }

  if (!employee) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center p-8 rounded-xl border border-gray-200 bg-white">
          <p className="text-lg font-semibold text-gray-700">
            Unable to load profile data.
          </p>
          <button
            onClick={logout}
            className="mt-4 text-gray-700 hover:underline"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-0">
      <header className="border-b shadow-sm bg-white border-gray-200">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center gap-6">
          <div className="flex-1 flex items-start gap-3">
            <div className="mt-1 p-2 rounded-lg bg-gray-100 text-gray-700">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
                Offboarding – Employee View
              </h1>
              <p className="text-sm font-medium text-gray-600">
                Track your tasks, handovers, and documentation
              </p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            {user && (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="p-2 rounded-full transition hover:bg-gray-100 text-gray-700"
                >
                  <User className="w-5 h-5" />
                </button>
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-52 rounded-lg border shadow-xl z-20 bg-white border-gray-200">
                      <div className="px-4 py-3 border-b border-gray-200">
                        <p className="text-sm font-medium text-gray-900">
                          {employee.name}
                        </p>
                        <p className="text-xs text-gray-600">
                          {employee.role}
                        </p>
                      </div>
                      <div className="p-2 space-y-1">
                        <button
                          onClick={() => {
                            logout();
                            setUserMenuOpen(false);
                          }}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition hover:bg-gray-100 text-gray-700"
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
              darkMode={false}
            />
          </aside>
          <main className="col-span-9 space-y-6">
            <div className="border rounded-lg shadow-sm p-2 bg-white border-gray-200">
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: "finalcall", label: "Final Call" },
                  { key: "handover", label: "Handover" },
                  { key: "documentation", label: "Documentation" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveSection(tab.key as SectionType)}
                    className={`py-3 rounded-lg text-sm font-semibold transition ${
                      activeSection === tab.key
                        ? "bg-gray-900 text-white shadow"
                        : "bg-gray-100 text-gray-900 hover:bg-gray-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-lg shadow border p-6 bg-white border-gray-200">
              {activeSection === "finalcall" && employee.employeeId && (
                <EmployeeFinalCallSection
                  employeeId={employee.employeeId}
                  darkMode={false}
                />
              )}
              {activeSection === "handover" && employee.employeeId && (
                <EmployeeHandoverSection
                  employeeId={employee.employeeId}
                  darkMode={false}
                />
              )}
              {activeSection === "documentation" && employee.employeeId && (
                <EmployeeDocumentationSection
                  employeeId={employee.employeeId}
                  darkMode={false}
                />
              )}
            </div>
          </main>
        </div>
      </div>
      <Chatbot role="offboarding" />
    </div>
  );
}
