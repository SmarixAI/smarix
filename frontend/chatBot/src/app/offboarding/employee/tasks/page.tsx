"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/components/auth/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import {
  Users,
  LogOut,
  MessageSquare,
  User,
  Moon,
  Sun,
  CheckCircle2,
  Calendar,
  Flag,
  Clock,
  ArrowRight,
  ListTodo,
} from "lucide-react";
import ThreeJsBackground from "@/components/onboarding/ThreeJsBackground";

// Point to your FastAPI Backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type TaskCategory = "all" | "onboarding" | "offboarding" | "day-to-day";
type TaskPriority = "high" | "medium" | "low";
type TaskStatus = "pending" | "in-progress" | "completed";

interface Task {
  id: string;
  title: string;
  description: string;
  category: "onboarding" | "offboarding" | "day-to-day";
  priority: TaskPriority;
  status: TaskStatus;
  deadline: string | null;
  assignedTo: string;
  createdAt: string;
}

function EmployeeTasksContent() {
  const { user, logout, token } = useAuth(); // Get Token
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  // 1. FETCH TASKS FROM BACKEND DB
  useEffect(() => {
    const fetchTasks = async () => {
      if (!user || !token) return;

      try {
        const response = await fetch(`${API_URL}/auth/tasks`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();

          // Map Backend (Snake Case) -> Frontend (Camel Case)
          const mappedTasks: Task[] = data.map((t: any) => ({
            id: t.id,
            title: t.title,
            description: t.description || "",
            category: t.category,
            priority: t.priority,
            status: t.status,
            deadline: t.deadline,
            // Logic: If assigned_by is "Self", show "Self". Else show Manager Name
            assignedTo: t.assigned_by === "Self" ? "Self" : "Manager",
            createdAt: t.created_at,
          }));

          setTasks(mappedTasks);
        } else {
          console.error("Failed to fetch tasks");
          setTasks([]);
        }
      } catch (error) {
        console.error("Error fetching tasks:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [user, token]);

  // 2. GENERIC UPDATE FUNCTION
  const updateTaskInBackend = async (taskId: string, updates: any) => {
    if (!token) return;
    try {
      await fetch(`${API_URL}/auth/tasks/${taskId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });
    } catch (e) {
      console.error("Failed to update task", e);
    }
  };

  // 3. EVENT HANDLERS
  const handleMarkAsDone = async (taskId: string) => {
    // Optimistic UI Update
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: "completed" } : t))
    );
    await updateTaskInBackend(taskId, { status: "completed" });
  };

  const handleSetDeadline = async (taskId: string, deadline: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, deadline } : t))
    );
    await updateTaskInBackend(taskId, { deadline });
  };

  const handleSetPriority = async (taskId: string, priority: TaskPriority) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, priority } : t))
    );
    await updateTaskInBackend(taskId, { priority });
  };

  // --- UI HELPERS (Unchanged) ---
  useEffect(() => {
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [darkMode]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    });
  };

  const handleSidebarClick = (path: string) => router.push(path);

  const getPriorityColor = (priority: TaskPriority) => {
    if (priority === "high")
      return darkMode
        ? "text-red-400 bg-red-900/30 border-red-700"
        : "text-red-700 bg-red-50 border-red-200";
    if (priority === "medium")
      return darkMode
        ? "text-yellow-400 bg-yellow-900/30 border-yellow-700"
        : "text-yellow-700 bg-yellow-50 border-yellow-200";
    return darkMode
      ? "text-green-400 bg-green-900/30 border-green-700"
      : "text-green-700 bg-green-50 border-green-200";
  };

  const getStatusColor = (status: TaskStatus) => {
    if (status === "completed")
      return darkMode
        ? "text-green-400 bg-green-900/30"
        : "text-green-700 bg-green-50";
    if (status === "in-progress")
      return darkMode
        ? "text-blue-400 bg-blue-900/30"
        : "text-blue-700 bg-blue-50";
    return darkMode ? "text-gray-400 bg-gray-800" : "text-gray-700 bg-gray-100";
  };

  // Filter based on Employee Status (Onboarding vs General)
  const filteredTasks = tasks.filter((task) => {
    if (!user || user.role !== "employee") return true;
    const status = user.status || "general";
    if (status === "general") return task.category === "day-to-day";
    if (status === "onboard")
      return task.category === "onboarding" || task.category === "day-to-day";
    if (status === "offboard")
      return task.category === "offboarding" || task.category === "day-to-day";
    return true;
  });

  return (
    <div
      className={`min-h-screen transition-colors duration-700 relative overflow-hidden ${
        darkMode
          ? "bg-gray-900 text-gray-100"
          : "bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 text-slate-900"
      }`}
      onMouseMove={handleMouseMove}
    >
      <ThreeJsBackground darkMode={darkMode} />
      <div
        className="fixed inset-0 pointer-events-none z-0 transition-all duration-300"
        style={{
          background: darkMode
            ? `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(99, 102, 241, 0.2) 0%, transparent 50%)`
            : `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(99, 102, 241, 0.15) 0%, transparent 50%)`,
        }}
      />

      <div className="flex h-screen overflow-hidden relative z-10">
        {/* SIDEBAR */}
        <aside
          className={`w-64 border-r transition-colors duration-300 ${
            darkMode
              ? "glass-card-dark border-gray-700"
              : "glass-card-light border-slate-200"
          }`}
        >
          <div className="p-6">
            <h2
              className={`text-lg font-bold mb-6 ${
                darkMode ? "text-gray-100" : "text-slate-900"
              }`}
            >
              Employee Dashboard
            </h2>
            <nav className="space-y-2">
              <div
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg ${
                  darkMode
                    ? "bg-indigo-600 text-white"
                    : "bg-indigo-600 text-white"
                }`}
              >
                <ListTodo className="w-5 h-5" />
                <span className="font-medium">Task Management</span>
              </div>
              <div className="pt-4 border-t border-gray-700 dark:border-gray-700">
                <p
                  className={`text-xs font-semibold uppercase tracking-wider mb-3 px-4 ${
                    darkMode ? "text-gray-400" : "text-slate-500"
                  }`}
                >
                  Navigate To
                </p>
                <div className="space-y-1">
                  {user?.status === "onboard" && (
                    <button
                      onClick={() => handleSidebarClick("/employee/onboarding")}
                      className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                        darkMode
                          ? "hover:bg-gray-800 text-gray-300"
                          : "hover:bg-indigo-50 text-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Users className="w-5 h-5" />
                        <span className="font-medium">Onboarding</span>
                      </div>
                      <ArrowRight className="w-4 h-4 opacity-60" />
                    </button>
                  )}
                  {user?.status === "offboard" && (
                    <button
                      onClick={() =>
                        handleSidebarClick("/employee/offboarding")
                      }
                      className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                        darkMode
                          ? "hover:bg-gray-800 text-gray-300"
                          : "hover:bg-indigo-50 text-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <LogOut className="w-5 h-5" />
                        <span className="font-medium">Offboarding</span>
                      </div>
                      <ArrowRight className="w-4 h-4 opacity-60" />
                    </button>
                  )}
                  <button
                    onClick={() => handleSidebarClick("/chat")}
                    className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                      darkMode
                        ? "hover:bg-gray-800 text-gray-300"
                        : "hover:bg-indigo-50 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-5 h-5" />
                      <span className="font-medium">General Chatbot</span>
                    </div>
                    <ArrowRight className="w-4 h-4 opacity-60" />
                  </button>
                </div>
              </div>
            </nav>
          </div>
        </aside>

        {/* MAIN AREA */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <header
            className={`border-b shadow-sm transition-colors duration-300 ${
              darkMode
                ? "glass-card-dark border-gray-700"
                : "glass-card-light border-slate-200"
            }`}
          >
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-xl ${
                    darkMode ? "bg-indigo-600" : "bg-indigo-200 text-indigo-700"
                  }`}
                >
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h1
                    className={`text-2xl font-extrabold tracking-tight ${
                      darkMode ? "text-gray-100" : "text-slate-900"
                    }`}
                  >
                    Task Management
                  </h1>
                  <p
                    className={`text-sm font-medium ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}
                  >
                    Manage all your tasks in one place
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
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
                      <div
                        className={`absolute right-0 mt-2 w-52 rounded-xl border shadow-xl z-100 ${
                          darkMode
                            ? "bg-gray-900 border-gray-700"
                            : "bg-white border-slate-200"
                        }`}
                      >
                        <div className="px-4 py-3 border-b dark:border-gray-700">
                          <p
                            className={`text-sm font-medium ${
                              darkMode ? "text-white" : "text-slate-900"
                            }`}
                          >
                            {user.name || user.username}
                          </p>
                          <p
                            className={`text-xs ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}
                          >
                            Employee
                          </p>
                        </div>
                        <div className="p-2 space-y-1">
                          <button
                            onClick={logout}
                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                              darkMode
                                ? "hover:bg-gray-800 text-gray-300"
                                : "hover:bg-indigo-50 text-slate-700"
                            }`}
                          >
                            <LogOut className="w-4 h-4" />
                            Logout
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="max-w-6xl mx-auto space-y-4">
              {loading ? (
                <div
                  className={`text-center py-12 rounded-xl ${
                    darkMode ? "glass-card-dark" : "glass-card-light"
                  }`}
                >
                  <p
                    className={`text-lg ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}
                  >
                    Loading tasks...
                  </p>
                </div>
              ) : filteredTasks.length === 0 ? (
                <div
                  className={`text-center py-12 rounded-xl ${
                    darkMode ? "glass-card-dark" : "glass-card-light"
                  }`}
                >
                  <p
                    className={`text-lg ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}
                  >
                    No tasks found
                  </p>
                </div>
              ) : (
                filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className={`rounded-xl border-2 p-6 transition-all duration-200 hover:shadow-lg ${
                      darkMode
                        ? "glass-card-dark border-gray-700"
                        : "glass-card-light border-slate-200"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3
                            className={`text-lg font-bold ${
                              darkMode ? "text-gray-100" : "text-slate-900"
                            }`}
                          >
                            {task.title}
                          </h3>
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(
                              task.priority
                            )}`}
                          >
                            {task.priority.toUpperCase()}
                          </span>
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(
                              task.status
                            )}`}
                          >
                            {task.status === "in-progress"
                              ? "In Progress"
                              : task.status.charAt(0).toUpperCase() +
                                task.status.slice(1)}
                          </span>
                        </div>
                        <p
                          className={`text-sm mb-3 ${
                            darkMode ? "text-gray-400" : "text-slate-600"
                          }`}
                        >
                          {task.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs">
                          <span
                            className={`flex items-center gap-1 ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}
                          >
                            <Users className="w-4 h-4" />
                            {task.assignedTo}
                          </span>
                          {task.deadline && (
                            <span
                              className={`flex items-center gap-1 ${
                                darkMode ? "text-gray-400" : "text-slate-500"
                              }`}
                            >
                              <Clock className="w-4 h-4" />
                              Deadline:{" "}
                              {new Date(task.deadline).toLocaleDateString()}
                            </span>
                          )}
                          <span
                            className={`${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}
                          >
                            Created:{" "}
                            {new Date(task.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 pt-4 border-t border-slate-200 dark:border-gray-700">
                      {task.status !== "completed" && (
                        <button
                          onClick={() => handleMarkAsDone(task.id)}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                            darkMode
                              ? "bg-green-900/30 text-green-400 hover:bg-green-900/50 border border-green-700"
                              : "bg-green-50 text-green-700 hover:bg-green-100 border border-green-200"
                          }`}
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          Mark as Done
                        </button>
                      )}
                      <button
                        onClick={() => {
                          const newDeadline = prompt(
                            "Enter deadline (YYYY-MM-DD):",
                            task.deadline || ""
                          );
                          if (newDeadline)
                            handleSetDeadline(task.id, newDeadline);
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                          darkMode
                            ? "bg-blue-900/30 text-blue-400 hover:bg-blue-900/50 border border-blue-700"
                            : "bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
                        }`}
                      >
                        <Calendar className="w-4 h-4" />
                        Set Deadline
                      </button>
                      <button
                        onClick={() => {
                          const nextP =
                            task.priority === "low"
                              ? "medium"
                              : task.priority === "medium"
                              ? "high"
                              : "low";
                          handleSetPriority(task.id, nextP);
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                          darkMode
                            ? "bg-purple-900/30 text-purple-400 hover:bg-purple-900/50 border border-purple-700"
                            : "bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200"
                        }`}
                      >
                        <Flag className="w-4 h-4" />
                        Toggle Priority
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EmployeeTasksPage() {
  return (
    <AuthProvider>
      <ProtectedRoute requiredRole="employee">
        <EmployeeTasksContent />
      </ProtectedRoute>
    </AuthProvider>
  );
}
