'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/components/auth/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { 
  Users, LogOut, MessageSquare, User, Moon, Sun, 
  CheckCircle2, Calendar, Flag, Filter, X, Clock, ArrowRight, ListTodo,
  UserCircle, Briefcase
} from 'lucide-react';
import ThreeJsBackground from '@/components/onboarding/ThreeJsBackground';

type TaskCategory = 'all' | 'onboarding' | 'offboarding' | 'day-to-day';
type TaskPriority = 'high' | 'medium' | 'low';
type TaskStatus = 'pending' | 'in-progress' | 'completed';

interface Task {
  id: string;
  title: string;
  description: string;
  category: 'onboarding' | 'offboarding' | 'day-to-day';
  priority: TaskPriority;
  status: TaskStatus;
  deadline: string | null;
  assignedTo: string;
  createdAt: string;
}

function ManagerTasksContent() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [activeSidebar, setActiveSidebar] = useState<'onboarding' | 'offboarding' | 'chatbot' | 'tasks' | 'my-onboarding' | 'my-offboarding'>('tasks');
  const [filterCategory, setFilterCategory] = useState<TaskCategory>('all');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  // Dummy tasks data
  useEffect(() => {
    const dummyTasks: Task[] = [
      // Onboarding tasks
      {
        id: '1',
        title: 'Setup new employee workspace',
        description: 'Configure laptop, access cards, and workspace for new hire',
        category: 'onboarding',
        priority: 'high',
        status: 'pending',
        deadline: '2025-01-15',
        assignedTo: 'IT Team',
        createdAt: '2025-01-10'
      },
      {
        id: '2',
        title: 'Schedule orientation session',
        description: 'Organize first-day orientation for new employees',
        category: 'onboarding',
        priority: 'medium',
        status: 'in-progress',
        deadline: '2025-01-20',
        assignedTo: 'HR Team',
        createdAt: '2025-01-08'
      },
      {
        id: '3',
        title: 'Prepare onboarding documentation',
        description: 'Create and review onboarding materials and guides',
        category: 'onboarding',
        priority: 'high',
        status: 'completed',
        deadline: '2025-01-12',
        assignedTo: 'Documentation Team',
        createdAt: '2025-01-05'
      },
      // Offboarding tasks
      {
        id: '4',
        title: 'Collect company assets',
        description: 'Retrieve laptop, access cards, and other company equipment',
        category: 'offboarding',
        priority: 'high',
        status: 'pending',
        deadline: '2025-01-18',
        assignedTo: 'IT Team',
        createdAt: '2025-01-11'
      },
      {
        id: '5',
        title: 'Conduct exit interview',
        description: 'Schedule and conduct final exit interview with departing employee',
        category: 'offboarding',
        priority: 'medium',
        status: 'in-progress',
        deadline: '2025-01-22',
        assignedTo: 'HR Team',
        createdAt: '2025-01-09'
      },
      {
        id: '6',
        title: 'Transfer knowledge and documentation',
        description: 'Ensure all project knowledge is documented and transferred',
        category: 'offboarding',
        priority: 'high',
        status: 'pending',
        deadline: '2025-01-25',
        assignedTo: 'Team Lead',
        createdAt: '2025-01-12'
      },
      // Day to day tasks
      {
        id: '7',
        title: 'Review weekly team performance',
        description: 'Analyze team metrics and provide feedback',
        category: 'day-to-day',
        priority: 'medium',
        status: 'pending',
        deadline: '2025-01-17',
        assignedTo: 'Self',
        createdAt: '2025-01-13'
      },
      {
        id: '8',
        title: 'Update project roadmap',
        description: 'Review and update project timeline and milestones',
        category: 'day-to-day',
        priority: 'high',
        status: 'in-progress',
        deadline: '2025-01-19',
        assignedTo: 'Project Manager',
        createdAt: '2025-01-10'
      },
      {
        id: '9',
        title: 'Conduct team standup meeting',
        description: 'Daily standup to discuss progress and blockers',
        category: 'day-to-day',
        priority: 'low',
        status: 'completed',
        deadline: '2025-01-14',
        assignedTo: 'Self',
        createdAt: '2025-01-14'
      },
      {
        id: '10',
        title: 'Approve pending leave requests',
        description: 'Review and approve employee leave applications',
        category: 'day-to-day',
        priority: 'medium',
        status: 'pending',
        deadline: '2025-01-16',
        assignedTo: 'Self',
        createdAt: '2025-01-13'
      }
    ];
    setTasks(dummyTasks);
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  // Close priority menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('[id^="priority-menu-"]') && !target.closest('button[onClick*="priority-menu"]')) {
        document.querySelectorAll('[id^="priority-menu-"]').forEach((menu) => {
          menu.classList.add('hidden');
        });
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleSidebarClick = (item: 'onboarding' | 'offboarding' | 'chatbot' | 'tasks' | 'my-onboarding' | 'my-offboarding') => {
    setActiveSidebar(item);
    if (item === 'chatbot') {
      router.push('/chat');
    } else if (item === 'onboarding') {
      // Navigate to onboarding manager view
      router.push('/manager/onboarding');
    } else if (item === 'offboarding') {
      router.push('/manager/offboarding');
    } else if (item === 'my-onboarding') {
      // Navigate to employee onboarding view (manager's own onboarding)
      router.push('/employee/onboarding');
    } else if (item === 'my-offboarding') {
      // Navigate to employee offboarding view (manager's own offboarding)
      router.push('/employee/offboarding');
    }
  };

  const handleMarkAsDone = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, status: 'completed' as TaskStatus }
        : task
    ));
  };

  const handleSetDeadline = (taskId: string, deadline: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, deadline }
        : task
    ));
  };

  const handleSetPriority = (taskId: string, priority: TaskPriority) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, priority }
        : task
    ));
  };

  const filteredTasks = filterCategory === 'all' 
    ? tasks 
    : tasks.filter(task => task.category === filterCategory);

  const getPriorityColor = (priority: TaskPriority) => {
    if (priority === 'high') {
      return darkMode ? 'text-red-400 bg-red-900/30 border-red-700' : 'text-red-700 bg-red-50 border-red-200';
    } else if (priority === 'medium') {
      return darkMode ? 'text-yellow-400 bg-yellow-900/30 border-yellow-700' : 'text-yellow-700 bg-yellow-50 border-yellow-200';
    } else {
      return darkMode ? 'text-green-400 bg-green-900/30 border-green-700' : 'text-green-700 bg-green-50 border-green-200';
    }
  };

  const getStatusColor = (status: TaskStatus) => {
    if (status === 'completed') {
      return darkMode ? 'text-green-400 bg-green-900/30' : 'text-green-700 bg-green-50';
    } else if (status === 'in-progress') {
      return darkMode ? 'text-blue-400 bg-blue-900/30' : 'text-blue-700 bg-blue-50';
    } else {
      return darkMode ? 'text-gray-400 bg-gray-800' : 'text-gray-700 bg-gray-100';
    }
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-700 relative overflow-hidden ${
        darkMode
          ? "bg-gray-900 text-gray-100"
          : "bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 text-slate-900"
      }`}
      onMouseMove={handleMouseMove}
    >
      <style jsx global>{`
        .glass-card-light {
          backdrop-filter: blur(20px) saturate(200%);
          -webkit-backdrop-filter: blur(20px) saturate(200%);
          background: rgba(255, 255, 255, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.5);
        }

        .glass-card-dark {
          backdrop-filter: blur(16px) saturate(180%);
          -webkit-backdrop-filter: blur(16px) saturate(180%);
          background: rgba(17, 24, 39, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
      `}</style>

      <ThreeJsBackground darkMode={darkMode} />

      <div
        className="fixed inset-0 pointer-events-none z-0 transition-all duration-300"
        style={{
          background: darkMode
            ? `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.2) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(139, 92, 246, 0.2) 0%, transparent 50%)`
            : `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(6, 182, 212, 0.15) 0%, transparent 50%)`,
        }}
      />

      <div className="flex h-screen overflow-hidden relative z-10">
        {/* SIDEBAR */}
        <aside className={`w-64 border-r transition-colors duration-300 ${
          darkMode
            ? "glass-card-dark border-gray-700"
            : "glass-card-light border-slate-200"
        }`}>
          <div className="p-6">
            <h2 className={`text-lg font-bold mb-6 ${
              darkMode ? "text-gray-100" : "text-slate-900"
            }`}>
              Manager Dashboard
            </h2>
            <nav className="space-y-2">
              {/* CURRENT PAGE - Task Management */}
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

              {/* MY ONBOARDING/OFFBOARDING SECTION - Only show if status is not 'general' */}
              {user && user.role === 'manager' && user.status && user.status !== 'general' && (
                <div className="pt-4 border-t border-gray-700 dark:border-gray-700">
                  <p className={`text-xs font-semibold uppercase tracking-wider mb-3 px-4 ${
                    darkMode ? "text-gray-400" : "text-slate-500"
                  }`}>
                    My Personal
                  </p>
                  <div className="space-y-1 mb-4">
                    {/* Show My Onboarding only if status is 'onboard' */}
                    {user.status === 'onboard' && (
                      <button
                        onClick={() => handleSidebarClick('my-onboarding')}
                        className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                          darkMode
                            ? "hover:bg-gray-800 text-gray-300"
                            : "hover:bg-indigo-50 text-slate-700"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <UserCircle className="w-5 h-5" />
                          <div className="flex flex-col items-start">
                            <span className="font-medium">My Onboarding</span>
                            <span className={`text-xs ${
                              darkMode ? "text-gray-500" : "text-slate-500"
                            }`}>
                              When I joined
                            </span>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 opacity-60" />
                      </button>
                    )}
                    {/* Show My Offboarding only if status is 'offboard' */}
                    {user.status === 'offboard' && (
                      <button
                        onClick={() => handleSidebarClick('my-offboarding')}
                        className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                          darkMode
                            ? "hover:bg-gray-800 text-gray-300"
                            : "hover:bg-indigo-50 text-slate-700"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <UserCircle className="w-5 h-5" />
                          <div className="flex flex-col items-start">
                            <span className="font-medium">My Offboarding</span>
                            <span className={`text-xs ${
                              darkMode ? "text-gray-500" : "text-slate-500"
                            }`}>
                              When I'm leaving
                            </span>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 opacity-60" />
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* NAVIGATION LINKS - MANAGING OTHERS */}
              <div className="pt-4 border-t border-gray-700 dark:border-gray-700">
                <p className={`text-xs font-semibold uppercase tracking-wider mb-3 px-4 ${
                  darkMode ? "text-gray-400" : "text-slate-500"
                }`}>
                  Manage Team
                </p>
                <div className="space-y-1">
                  <button
                    onClick={() => handleSidebarClick('onboarding')}
                    className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                      darkMode
                        ? "hover:bg-gray-800 text-gray-300"
                        : "hover:bg-indigo-50 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Users className="w-5 h-5" />
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Manage Onboarding</span>
                        <span className={`text-xs ${
                          darkMode ? "text-gray-500" : "text-slate-500"
                        }`}>
                          Team members
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 opacity-60" />
                  </button>
                  <button
                    onClick={() => handleSidebarClick('offboarding')}
                    className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-left transition ${
                      darkMode
                        ? "hover:bg-gray-800 text-gray-300"
                        : "hover:bg-indigo-50 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <LogOut className="w-5 h-5" />
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Manage Offboarding</span>
                        <span className={`text-xs ${
                          darkMode ? "text-gray-500" : "text-slate-500"
                        }`}>
                          Team members
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 opacity-60" />
                  </button>
                  <button
                    onClick={() => handleSidebarClick('chatbot')}
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

        {/* MAIN CONTENT */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* HEADER */}
          <header className={`border-b shadow-sm transition-colors duration-300 ${
            darkMode
              ? "glass-card-dark border-gray-700"
              : "glass-card-light border-slate-200"
          }`}>
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl ${
                  darkMode ? "bg-indigo-600" : "bg-indigo-200 text-indigo-700"
                }`}>
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h1 className={`text-2xl font-extrabold tracking-tight ${
                    darkMode ? "text-gray-100" : "text-slate-900"
                  }`}>
                    Task Management
                  </h1>
                  <p className={`text-sm font-medium ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`}>
                    Manage all your tasks in one place
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* THEME TOGGLE */}
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className={`p-2 rounded-lg transition ${
                    darkMode
                      ? "hover:bg-gray-800 text-yellow-400"
                      : "hover:bg-indigo-50 text-indigo-600"
                  }`}
                  title={darkMode ? "Light mode" : "Dark mode"}
                >
                  {darkMode ? (
                    <Sun className="w-5 h-5" />
                  ) : (
                    <Moon className="w-5 h-5" />
                  )}
                </button>

                {/* USER MENU */}
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
                              Manager
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
                              <LogOut className="w-4 h-4" />
                              Logout
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

          {/* FILTER BAR */}
          <div className={`px-6 py-4 border-b transition-colors duration-300 ${
            darkMode
              ? "glass-card-dark border-gray-700"
              : "glass-card-light border-slate-200"
          }`}>
            <div className="flex items-center gap-4">
              <Filter className={`w-5 h-5 ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`} />
              <span className={`text-sm font-medium ${
                darkMode ? "text-gray-300" : "text-slate-700"
              }`}>
                Filter:
              </span>
              <div className="flex gap-2">
                {(['all', 'onboarding', 'offboarding', 'day-to-day'] as TaskCategory[]).map((category) => (
                  <button
                    key={category}
                    onClick={() => setFilterCategory(category)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                      filterCategory === category
                        ? darkMode
                          ? "bg-indigo-600 text-white"
                          : "bg-indigo-600 text-white"
                        : darkMode
                          ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                          : "bg-white text-slate-700 hover:bg-indigo-50 border border-slate-200"
                    }`}
                  >
                    {category === 'all' ? 'All Tasks' : 
                     category === 'day-to-day' ? 'Day to Day' :
                     category.charAt(0).toUpperCase() + category.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* TASKS LIST */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="max-w-6xl mx-auto space-y-4">
              {filteredTasks.length === 0 ? (
                <div className={`text-center py-12 rounded-xl ${
                  darkMode ? "glass-card-dark" : "glass-card-light"
                }`}>
                  <p className={`text-lg ${
                    darkMode ? "text-gray-400" : "text-slate-600"
                  }`}>
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
                          <h3 className={`text-lg font-bold ${
                            darkMode ? "text-gray-100" : "text-slate-900"
                          }`}>
                            {task.title}
                          </h3>
                          <span className={`px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(task.priority)}`}>
                            {task.priority.toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(task.status)}`}>
                            {task.status === 'in-progress' ? 'In Progress' : task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                          </span>
                        </div>
                        <p className={`text-sm mb-3 ${
                          darkMode ? "text-gray-400" : "text-slate-600"
                        }`}>
                          {task.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs">
                          <span className={`flex items-center gap-1 ${
                            darkMode ? "text-gray-400" : "text-slate-500"
                          }`}>
                            <Users className="w-4 h-4" />
                            {task.assignedTo}
                          </span>
                          {task.deadline && (
                            <span className={`flex items-center gap-1 ${
                              darkMode ? "text-gray-400" : "text-slate-500"
                            }`}>
                              <Clock className="w-4 h-4" />
                              Deadline: {new Date(task.deadline).toLocaleDateString()}
                            </span>
                          )}
                          <span className={`${
                            darkMode ? "text-gray-400" : "text-slate-500"
                          }`}>
                            Created: {new Date(task.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* ACTION BUTTONS */}
                    <div className="flex items-center gap-2 pt-4 border-t border-slate-200 dark:border-gray-700">
                      {task.status !== 'completed' && (
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
                          const newDeadline = prompt('Enter deadline (YYYY-MM-DD):', task.deadline || '');
                          if (newDeadline) {
                            handleSetDeadline(task.id, newDeadline);
                          }
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
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const priorityMenu = document.getElementById(`priority-menu-${task.id}`);
                            if (priorityMenu) {
                              // Close all other menus
                              document.querySelectorAll('[id^="priority-menu-"]').forEach((menu) => {
                                if (menu.id !== `priority-menu-${task.id}`) {
                                  menu.classList.add('hidden');
                                }
                              });
                              priorityMenu.classList.toggle('hidden');
                            }
                          }}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                            darkMode
                              ? "bg-purple-900/30 text-purple-400 hover:bg-purple-900/50 border border-purple-700"
                              : "bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200"
                          }`}
                        >
                          <Flag className="w-4 h-4" />
                          Set Priority
                        </button>
                        <div
                          id={`priority-menu-${task.id}`}
                          className={`hidden absolute left-0 mt-2 w-32 rounded-lg shadow-xl z-20 ${
                            darkMode
                              ? "bg-gray-800 border border-gray-700"
                              : "bg-white border border-slate-200"
                          }`}
                        >
                          {(['high', 'medium', 'low'] as TaskPriority[]).map((priority) => (
                            <button
                              key={priority}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSetPriority(task.id, priority);
                                const menu = document.getElementById(`priority-menu-${task.id}`);
                                if (menu) menu.classList.add('hidden');
                              }}
                              className={`w-full text-left px-4 py-2 text-sm transition first:rounded-t-lg last:rounded-b-lg ${
                                darkMode
                                  ? "text-gray-300 hover:bg-gray-700"
                                  : "text-slate-700 hover:bg-indigo-50"
                              }`}
                            >
                              {priority.charAt(0).toUpperCase() + priority.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
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

export default function ManagerTasksPage() {
  return (
    <AuthProvider>
      <ProtectedRoute requiredRole="manager">
        <ManagerTasksContent />
      </ProtectedRoute>
    </AuthProvider>
  );
}

