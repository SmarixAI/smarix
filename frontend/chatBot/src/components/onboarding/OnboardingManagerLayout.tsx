"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Moon,
  Sun,
  User,
  LogOut,
  UserPlus,
  CheckCircle,
} from "lucide-react";
import Loader from "../offboarding/Loader";
import { useAuth } from "@/components/auth/AuthContext";
import OnboardingEmployeeSwitcher from "./OnboardingEmployeeSwitcher";
import OnboardingSidebar from "./OnboardingSidebar";
import ReadingSection from "./managerViewSections/ReadingSection";
import QASection from "./managerViewSections/QASection";
import PracticeSection from "./managerViewSections/PracticeSection";
import BugFixSection from "./managerViewSections/BugFixSection";

const API_URL = "http://localhost:8000";

type SectionType = "reading" | "qa" | "practice" | "bugfix";
type ViewType = "dashboard" | "manage";

type Employee = {
  id: string;
  employeeId: string;
  name: string;
  role: string;
  status: string;
  lastDay: string | null;
  username: string;
};

type OnboardingManagerLayoutProps = {
  darkMode?: boolean;
  setDarkMode?: (value: boolean) => void;
};

export default function OnboardingManagerLayout({
  darkMode = false,
  setDarkMode,
}: OnboardingManagerLayoutProps = {}) {
  const { user, logout, token } = useAuth();
  const [view, setView] = useState<ViewType>("dashboard");
  const [onboardingEmployees, setOnboardingEmployees] = useState<Employee[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(
    null
  );
  const [activeSection, setActiveSection] = useState<SectionType>("reading");

  const fetchEmployees = async () => {
    try {
      console.log("--- DEBUG START: Fetching Employees ---");
      console.log("Current User Context:", user);

      if (!user?.employeeId || !token) {
        console.warn("ABORT: Missing employeeId or Token. Are you logged in?");
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        console.error("API Error Status:", response.status);
        setLoading(false);
        return;
      }

      const allUsers = await response.json();
      console.log("Raw API Response (All Users):", allUsers);

      const managerId = user.employeeId;
      console.log("Filtering for Manager ID:", managerId);

      const filtered = allUsers.filter((u: any) => {
        // --- DEFENSIVE CHECKS ---
        const role = u.role?.toLowerCase() || "";
        const status = u.status?.toLowerCase() || "";
        const managers = u.managers || []; // Fallback to empty array if null

        const isEmployee = role === "employee";
        const isOnboard = status === "onboard";
        const isManagedByMe =
          Array.isArray(managers) && managers.includes(managerId);

        if (isEmployee && isOnboard) {
          console.log(
            `Checking candidate: ${u.username} | Managers: ${managers} | Match? ${isManagedByMe}`
          );
        }

        return isEmployee && isOnboard && isManagedByMe;
      });

      console.log("Filtered List:", filtered);

      const mappedEmployees: Employee[] = filtered.map((u: any) => ({
        id: u.id,
        // API sends 'employee_id' (snake_case), map to 'employeeId' (camelCase)
        employeeId: u.employee_id || u.employeeId || "UNKNOWN",
        name: u.name || u.username,
        username: u.username,
        role: u.designation || "Employee",
        status: u.status,
        lastDay: u.last_day,
      }));

      setOnboardingEmployees(mappedEmployees);

      if (mappedEmployees.length > 0 && !selectedEmployee) {
        setSelectedEmployee(mappedEmployees[0]);
      }
    } catch (error) {
      console.error("Error fetching employees:", error);
    } finally {
      setLoading(false);
      console.log("--- DEBUG END ---");
    }
  };

  const finishOnboarding = async (employee: Employee) => {
    try {
      if (!token) return;
      const response = await fetch(
        `${API_URL}/auth/users/${employee.username}/status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status: "general" }),
        }
      );

      if (response.ok) {
        alert(`Finished onboarding for ${employee.name}`);
        fetchEmployees();
      } else {
        alert("Failed to update status");
      }
    } catch (error) {
      alert("Network error");
    }
  };

  useEffect(() => {
    // Only fetch if user data is loaded
    if (user) {
      fetchEmployees();
    }
  }, [user, token]);

  if (loading)
    return <Loader darkMode={darkMode} message="Loading..." fullScreen />;

  return (
    <div className="min-h-screen pt-0">
      {/* HEADER */}
      <header
        className={`backdrop-blur-lg border-b sticky top-0 z-50 transition-colors duration-300 ${
          darkMode
            ? "glass-card-dark border-gray-700"
            : "glass-card-light border-slate-200/50"
        }`}
      >
        <div className="max-w-screen-2xl mx-auto px-6 py-5 flex items-center gap-6">
          <div className="flex-1 flex items-start gap-4">
            <div className="mt-1 p-3 rounded-2xl bg-indigo-600 text-white">
              <UserPlus className="w-6 h-6" />
            </div>
            <div>
              <h1
                className={`text-2xl font-bold ${
                  darkMode ? "text-white" : "text-slate-900"
                }`}
              >
                Onboarding Manager
              </h1>
              <p
                className={`text-sm ${
                  darkMode ? "text-gray-400" : "text-slate-600"
                }`}
              >
                Manage team progress
              </p>
            </div>
          </div>
          <button
            onClick={() =>
              setView(view === "dashboard" ? "manage" : "dashboard")
            }
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-slate-900 font-semibold shadow-md"
          >
            <Users className="w-4 h-4" />{" "}
            {view === "dashboard" ? "Manage List" : "Dashboard"}
          </button>
          {user && (
            <div className="flex items-center gap-4">
              <div
                className={`text-right text-sm ${
                  darkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                <p className="font-bold">{user.username}</p>
                <p className="text-xs opacity-70">ID: {user.employeeId}</p>
              </div>
              <button
                onClick={logout}
                className="p-2 bg-red-500/20 text-red-500 rounded-lg"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* CONTENT */}
      <div className="p-6 max-w-screen-2xl mx-auto">
        {onboardingEmployees.length === 0 ? (
          <div
            className={`p-12 text-center rounded-3xl border ${
              darkMode
                ? "border-gray-700 bg-gray-800/50"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <h3
              className={`text-xl font-bold ${
                darkMode ? "text-white" : "text-slate-900"
              }`}
            >
              No Data Found
            </h3>
            <p
              className={`mt-2 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}
            >
              We couldn't find any employees with status{" "}
              <strong>"onboard"</strong> assigned to Manager ID:{" "}
              <strong>{user?.employeeId || "None"}</strong>.
            </p>
            <button
              onClick={fetchEmployees}
              className="mt-6 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Retry Fetch
            </button>
          </div>
        ) : (
          <>
            {view === "manage" ? (
              <div className="space-y-4">
                {onboardingEmployees.map((emp) => (
                  <div
                    key={emp.id}
                    className={`flex items-center justify-between p-6 rounded-2xl border ${
                      darkMode
                        ? "bg-gray-800 border-gray-700"
                        : "bg-white border-slate-200"
                    }`}
                  >
                    <div>
                      <h3
                        className={`text-lg font-bold ${
                          darkMode ? "text-white" : "text-slate-900"
                        }`}
                      >
                        {emp.name}
                      </h3>
                      <p
                        className={`text-sm ${
                          darkMode ? "text-gray-400" : "text-slate-500"
                        }`}
                      >
                        {emp.role}
                      </p>
                    </div>
                    <button
                      onClick={() => finishOnboarding(emp)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" /> Finish Onboarding
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-12 gap-6">
                <aside className="col-span-3">
                  <OnboardingEmployeeSwitcher
                    employees={onboardingEmployees}
                    selected={selectedEmployee}
                    onSelect={setSelectedEmployee}
                    darkMode={darkMode}
                  />
                  {selectedEmployee && (
                    <OnboardingSidebar
                      activeSection={activeSection}
                      onChangeSection={setActiveSection}
                      selectedEmployee={selectedEmployee}
                      darkMode={darkMode}
                    />
                  )}
                </aside>
                <main className="col-span-9">
                  {selectedEmployee && (
                    <div
                      className={`p-6 rounded-2xl border ${
                        darkMode
                          ? "bg-gray-800 border-gray-700"
                          : "bg-white border-slate-200"
                      }`}
                    >
                      {activeSection === "reading" && (
                        <ReadingSection
                          employeeId={selectedEmployee.employeeId}
                          darkMode={darkMode}
                        />
                      )}
                      {activeSection === "qa" && (
                        <QASection
                          employeeId={selectedEmployee.employeeId}
                          darkMode={darkMode}
                        />
                      )}
                      {activeSection === "practice" && (
                        <PracticeSection
                          employeeId={selectedEmployee.employeeId}
                          darkMode={darkMode}
                        />
                      )}
                      {activeSection === "bugfix" && (
                        <BugFixSection
                          employeeId={selectedEmployee.employeeId}
                          darkMode={darkMode}
                        />
                      )}
                    </div>
                  )}
                </main>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
