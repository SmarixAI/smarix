'use client';

import { useState, useEffect, useMemo } from 'react';
import { Briefcase, Users, Moon, Sun, User, ArrowLeft, Search } from 'lucide-react';

import EmployeeSwitcher from './EmployeeSwitcher';
import Sidebar from './Sidebar';
import FinalCallSection from './managerViewSections/FinalCallSection';
import HandoverSection from './managerViewSections/HandoverSection';
import DocumentationSection from './managerViewSections/DocumentationSection';
import Loader from './Loader';
import { useAuth } from '@/components/auth/AuthContext';

/* ================= TYPES ================= */

type SectionType = 'finalcall' | 'handover' | 'documentation';
type ViewType = 'dashboard' | 'manage';

type Employee = {
  id: string;
  employeeId?: string; // For compatibility with child components
  name: string;
  role: string;
  designation?: string; // Designation from users.json
  risk: 'high' | 'medium' | 'low';
  status: 'active' | 'leaving';
  lastDay: string | null;
};

/* ================= COMPONENT ================= */

type OffboardingManagerLayoutProps = {
  darkMode?: boolean;
  setDarkMode?: (value: boolean) => void;
};

export default function OffboardingManagerLayout({ darkMode = false, setDarkMode }: OffboardingManagerLayoutProps = {}) {
  const { user, logout } = useAuth();
  const [view, setView] = useState<ViewType>('dashboard');
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [allUsersEmployees, setAllUsersEmployees] = useState<any[]>([]); // All employees from users.json
  const [loading, setLoading] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const [offboardingEmployees, setOffboardingEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(
    null
  );
  const [searchQuery, setSearchQuery] = useState('');

  const [activeSection, setActiveSection] =
    useState<SectionType>('finalcall');

  const fetchEmployees = async () => {
    try {
      // Get logged-in manager's employeeId
      const managerEmployeeId = user?.employeeId;
      
      if (!managerEmployeeId) {
        console.warn('Manager employeeId not found - showing no employees. Manager must have employeeId set in users.json');
        setOffboardingEmployees([]);
        setAllUsersEmployees([]);
        setEmployees([]);
        setLoading(false);
        return;
      }
      
      // Fetch all employees from 1employees_with_ids.json
      const empResponse = await fetch('/api/offboarding/employees');
      if (!empResponse.ok) {
        console.error('Failed to fetch employees data');
        setLoading(false);
        return;
      }
      const empData = await empResponse.json();
      
      // Fetch users to get status
      const usersResponse = await fetch('/api/users');
      let usersData = { users: [] };
      try {
        if (usersResponse.ok) {
          usersData = await usersResponse.json();
        }
      } catch (e) {
        console.error('Error fetching users:', e);
      }

      if (empData.employees) {
        setEmployees(empData.employees);
        
        // Get all employees from users.json for manage view - filter by manager relationship
        const allEmployeeUsers = usersData.users.filter((u: any) => {
          if (u.role !== 'employee') return false;
          // Check if manager's employeeId is in employee's managers array
          const employeeManagers = u.managers || [];
          return employeeManagers.includes(managerEmployeeId);
        });
        setAllUsersEmployees(allEmployeeUsers);
        
        // Filter employees with status "offboard" AND where manager's employeeId is in their managers array
        const offboardUsers = usersData.users.filter((u: any) => {
          const isOffboardEmployee = u.role === 'employee' && u.status === 'offboard';
          if (!isOffboardEmployee) return false;
          // Check if manager's employeeId is in employee's managers array
          const employeeManagers = u.managers || [];
          return employeeManagers.includes(managerEmployeeId);
        });
        
        // Match employees - check both employeeId and employee_id fields, and name
        // Also merge lastDay from users.json into employee data
        const offboarding = empData.employees
          .filter((emp: Employee) => {
            const empId = emp.employeeId;
            const empName = emp.name;
            return offboardUsers.some((u: any) => {
              const userId = u.employeeId;
              const userName = u.name || u.username;
              return (
                (userId && userId === empId) ||
                (userName && userName === empName) ||
                (userName && empName && userName.toLowerCase() === empName.toLowerCase())
              );
            });
          })
          .map((emp: Employee) => {
            // Find matching user to get lastDay, designation, and other details from users.json
            const matchingUser = offboardUsers.find((u: any) => {
              const userId = u.employeeId;
              const userName = u.name || u.username;
              const empId = emp.employeeId;
              const empName = emp.name;
              return (
                (userId && userId === empId) ||
                (userName && userName === empName) ||
                (userName && empName && userName.toLowerCase() === empName.toLowerCase())
              );
            });
            
            // Merge user details from users.json (lastDay, designation, etc.)
            if (matchingUser) {
              return { 
                ...emp, 
                employeeId: emp.employeeId || matchingUser.employeeId, // Ensure employeeId is set
                lastDay: matchingUser.lastDay || emp.lastDay,
                role: matchingUser.designation || emp.role, // Use designation as role
                designation: matchingUser.designation || emp.role
              };
            }
            // Ensure employeeId is set even if no matching user
            return {
              ...emp,
              employeeId: emp.employeeId
            };
          });
        
        setOffboardingEmployees(offboarding);
        
        // Find first employee with status "offboard"
        if (offboarding.length > 0) {
          const firstEmployee = offboarding[0];
          console.log('Manager - Setting selected employee:', {
            employeeId: firstEmployee.employeeId || firstEmployee.employee_id,
            id: firstEmployee.id,
            name: firstEmployee.name
          });
          setSelectedEmployee(firstEmployee);
        } else {
          console.log('Manager - No offboarding employees found');
          setSelectedEmployee(null);
        }
      }
    } catch (error) {
      console.error('Error fetching employees data:', error);
    } finally {
      setLoading(false);
    }
  };

  const markEmployeeAsLeaving = async (usernameOrId: string, date: string) => {
    try {
      // Find the user in allUsersEmployees
      const user = allUsersEmployees.find((u: any) => 
        u.username === usernameOrId || 
        u.employeeId === usernameOrId ||
        u.name === usernameOrId
      );
      
      if (!user) {
        alert('Employee not found in users list');
        return;
      }
      
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: user.username,
          status: 'offboard',
          lastDay: date,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to update employee status:', errorData);
        alert(`Failed to update employee status: ${errorData.error || 'Unknown error'}`);
        return;
      }

      // Refresh the employees list to get updated data
      await fetchEmployees();
      
      alert('Employee marked as leaving successfully!');
    } catch (error) {
      console.error('Error updating employee status:', error);
      alert('Error updating employee status. Please try again.');
    }
  };

  // Filter and sort employees - leaving employees at top
  const filteredEmployees = useMemo(() => {
    let filtered = allUsersEmployees;
    
    // Apply search filter if query exists
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = allUsersEmployees.filter((user: any) => {
        const name = (user.name || user.username || '').toLowerCase();
        const designation = (user.designation || '').toLowerCase();
        const employeeId = (user.employeeId || '').toLowerCase();
        const username = (user.username || '').toLowerCase();
        return name.includes(query) || 
               designation.includes(query) || 
               employeeId.includes(query) ||
               username.includes(query);
      });
    }
    
    // Sort: leaving employees (status === 'offboard') first, then others
    return filtered.sort((a: any, b: any) => {
      const aIsLeaving = a.status === 'offboard';
      const bIsLeaving = b.status === 'offboard';
      
      if (aIsLeaving && !bIsLeaving) return -1;
      if (!aIsLeaving && bIsLeaving) return 1;
      return 0; // Keep original order for same status
    });
  }, [allUsersEmployees, searchQuery]);

  /* 🔹 Load employees data */
  useEffect(() => {
    if (user?.employeeId) {
      fetchEmployees();
    }
  }, [user]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading offboarding data..." fullScreen />;
  }

  return (
    <div className="min-h-screen pt-0">

      {/* ================= HEADER ================= */}
      <header className={`backdrop-blur-lg border-b sticky top-0 z-50 transition-colors duration-300 ${
        darkMode
          ? "glass-card-dark border-gray-700 shadow-lg shadow-gray-900/20"
          : "glass-card-light border-slate-200/50 shadow-lg shadow-indigo-100/20"
      }`}>
        <div className="max-w-screen-2xl mx-auto px-6 py-5 flex items-center gap-6">

          {/* LEFT */}
          <div className="flex-1 flex items-start gap-4">
            <div className="mt-1 p-3 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 transform transition-transform hover:scale-105">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <h1 className={`text-2xl font-extrabold tracking-tight ${
                darkMode
                  ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
                  : "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent"
              }`}>
                Offboarding – Manager View
              </h1>
              <p className={`text-sm font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Reduce risk and ensure clean handovers
              </p>
            </div>
          </div>

          {/* CENTER ACTION */}
          <button
            onClick={() =>
              setView(view === 'dashboard' ? 'manage' : 'dashboard')
            }
            className={`
              flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold
              shadow-md hover:shadow-lg transition-all duration-200
              transform hover:scale-105
              ${darkMode
                ? "bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-gray-100"
                : "bg-gradient-to-r from-slate-100 to-slate-200 hover:from-slate-200 hover:to-slate-300 text-slate-900"
              }
            `}
          >
            <Users className="w-4 h-4" />
            {view === 'dashboard'
              ? 'Manage Offboardings'
              : 'Back to Dashboard'}
          </button>

          {/* RIGHT */}
          <div className="flex items-center gap-4">
            {/* THEME TOGGLE */}
            {setDarkMode && (
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
            )}

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
                      className={`absolute right-0 mt-2 w-52 rounded-xl border shadow-xl z-20 ${
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
                            setUserMenuOpen(false);
                            logout();
                          }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                            darkMode
                              ? "hover:bg-gray-800 text-gray-300"
                              : "hover:bg-indigo-50 text-slate-700"
                          }`}
                        >
                          <ArrowLeft className="w-4 h-4" />
                          Go Back
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

      {/* ================= CONTENT ================= */}
      <div className="p-6 max-w-screen-2xl mx-auto">

        {/* ============ MANAGE OFFBOARDINGS VIEW ============ */}
        {view === 'manage' && (
          <div className={`backdrop-blur-lg rounded-3xl shadow-xl p-8 space-y-6 animate-fadeIn transition-colors duration-300 ${
            darkMode
              ? "glass-card-dark border border-gray-700"
              : "glass-card-light border border-slate-200/50"
          }`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                  <Users className="w-5 h-5" />
                </div>
                <h2 className={`text-3xl font-bold ${
                  darkMode
                    ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
                    : "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent"
                }`}>
                  Manage Employees
                </h2>
              </div>
            </div>

            {/* Search Bar */}
            <div className="relative">
              <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name, designation, employee ID, or username..."
                className={`w-full pl-12 pr-4 py-3 rounded-xl border outline-none transition-colors ${
                  darkMode
                    ? "bg-gray-700 text-white border-gray-600 focus:border-indigo-500 placeholder-gray-500"
                    : "bg-white text-slate-900 border-slate-300 focus:border-indigo-500 placeholder-slate-400"
                }`}
              />
            </div>

            <div className="grid gap-4">
              {filteredEmployees.length === 0 ? (
                    <div className={`text-center py-12 rounded-2xl ${
                      darkMode ? "glass-card-dark" : "glass-card-light"
                    }`}>
                      <p className={`text-lg font-medium ${
                        darkMode ? "text-gray-400" : "text-slate-600"
                      }`}>
                        {searchQuery ? 'No employees match your search' : 'No employees found'}
                      </p>
                    </div>
                  ) : (
                    filteredEmployees.map((user: any) => {
                  // Find matching employee from employees list for role/risk info
                  const matchingEmp = employees.find((emp: Employee) => {
                    const empId = emp.employeeId;
                    const empName = emp.name;
                    return (
                      (user.employeeId && user.employeeId === empId) ||
                      (user.name && user.name === empName) ||
                      (user.username && user.username === empName)
                    );
                  });
                  
                  const displayName = user.name || user.username;
                  const displayRole = user.designation || matchingEmp?.role || 'Employee';
                  const isOffboarding = user.status === 'offboard';
                  
                  return (
                    <div
                      key={user.username || user.employeeId}
                      className={`
                        flex items-center justify-between rounded-2xl p-5
                        shadow-md hover:shadow-xl transition-all duration-300
                        transform hover:scale-[1.02]
                        ${darkMode
                          ? "border border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900"
                          : "border border-slate-200 bg-gradient-to-r from-white to-slate-50/50"
                        }
                      `}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 text-white flex items-center justify-center font-bold text-lg shadow-lg">
                          {displayName.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p className={`font-bold text-lg ${
                            darkMode ? "text-gray-100" : "text-slate-900"
                          }`}>
                            {displayName}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <p className={`text-sm font-medium ${
                              darkMode ? "text-gray-400" : "text-slate-600"
                            }`}>
                              {displayRole}
                            </p>
                            {user.employeeId && (
                              <>
                                <span className={`text-xs ${
                                  darkMode ? "text-gray-500" : "text-slate-400"
                                }`}>•</span>
                                <p className={`text-xs font-medium ${
                                  darkMode ? "text-gray-500" : "text-slate-500"
                                }`}>
                                  ID: {user.employeeId}
                                </p>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {isOffboarding ? (
                        <div className={`px-4 py-2 rounded-xl border-2 ${
                          darkMode
                            ? "bg-red-900/30 border-red-700"
                            : "bg-red-50 border-red-200"
                        }`}>
                          <span className={`text-sm font-bold ${
                            darkMode ? "text-red-300" : "text-red-700"
                          }`}>
                            {user.lastDay && user.lastDay !== 'null' && user.lastDay !== null
                              ? `Leaving on ${user.lastDay}`
                              : 'Offboarding'}
                          </span>
                        </div>
                      ) : (
                        <div className="flex gap-3 items-center">
                          <input
                            type="date"
                            data-username={user.username}
                            className={`
                              border-2 rounded-xl px-4 py-2 text-sm
                              focus:outline-none focus:ring-2 focus:border-transparent
                              transition-all duration-200
                              ${darkMode
                                ? "border-gray-600 bg-gray-700 text-gray-100 focus:ring-indigo-400"
                                : "border-slate-300 text-slate-900 focus:ring-indigo-500"
                              }
                            `}
                          />
                          <button
                            onClick={() => {
                              const dateInput = document.querySelector(`input[data-username="${user.username}"]`) as HTMLInputElement;
                              if (dateInput && dateInput.value) {
                                markEmployeeAsLeaving(user.username, dateInput.value);
                              } else {
                                alert('Please select a date first');
                              }
                            }}
                            className={`
                              px-5 py-2.5 rounded-xl text-white text-sm font-semibold
                              shadow-lg hover:shadow-xl transition-all duration-200
                              transform hover:scale-105
                              ${darkMode
                                ? "bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600"
                                : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                              }
                            `}
                          >
                            Mark Leaving
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* ============ DASHBOARD VIEW ============ */}
        {view === 'dashboard' && (
          <div className="grid grid-cols-12 gap-6">

            {/* SIDEBAR */}
            <aside className="col-span-3 space-y-6">
              {offboardingEmployees.length > 0 ? (
                <EmployeeSwitcher
                  employees={offboardingEmployees}
                  selected={selectedEmployee}
                  onSelect={setSelectedEmployee}
                  darkMode={darkMode}
                />
              ) : (
                <div className={`rounded-2xl shadow-md border p-4 transition-colors duration-300 ${
                  darkMode
                    ? "glass-card-dark border-gray-700"
                    : "glass-card-light border-slate-200"
                }`}>
                  <div className={`border-b pb-3 ${
                    darkMode ? "border-gray-700" : ""
                  }`}>
                    <h3 className={`text-sm font-bold ${
                      darkMode ? "text-gray-100" : "text-slate-900"
                    }`}>
                      Active Offboardings
                    </h3>
                    <p className={`text-xs mt-1 ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      Employees currently in exit process
                    </p>
                  </div>
                  <div className="py-6 text-center">
                    <p className={`text-sm ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      No active offboardings. Mark employees as leaving in the "Manage Offboardings" view.
                    </p>
                  </div>
                </div>
              )}

              {selectedEmployee && (
                <Sidebar
                  activeSection={activeSection}
                  onChangeSection={setActiveSection}
                  selectedEmployee={selectedEmployee}
                  darkMode={darkMode}
                />
              )}
            </aside>

            {/* MAIN */}
            <main className="col-span-9 space-y-6">

              {/* TABS */}
              <div className={`backdrop-blur-lg border rounded-2xl shadow-lg p-1.5 transition-colors duration-300 ${
                darkMode
                  ? "bg-gray-800/80 border-gray-700"
                  : "bg-white/80 border-slate-200/50"
              }`}>
                <div className="grid grid-cols-3 gap-1.5">
                  {[
                    { key: 'finalcall', label: 'Final Call' },
                    { key: 'handover', label: 'Handover' },
                    { key: 'documentation', label: 'Documentation' }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() =>
                        setActiveSection(tab.key as SectionType)
                      }
                      className={`
                        py-2.5 rounded-xl text-xs font-bold transition-all duration-300
                        ${
                          activeSection === tab.key
                            ? darkMode
                              ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md shadow-indigo-500/30'
                              : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/30'
                            : darkMode
                              ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                        }
                      `}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

      {/* CONTENT */}
      {selectedEmployee ? (
        <div className={`backdrop-blur-lg rounded-2xl shadow-xl border p-4 animate-fadeIn transition-colors duration-300 ${
          darkMode
            ? "bg-gray-800/80 border-gray-700"
            : "bg-white/80 border-slate-200/50"
        }`}>
                  {activeSection === 'finalcall' && selectedEmployee && (
                    <FinalCallSection 
                      employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                      darkMode={darkMode} 
                    />
                  )}
                  {activeSection === 'handover' && selectedEmployee && (
                    <HandoverSection 
                      employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                      darkMode={darkMode} 
                    />
                  )}
                  {activeSection === 'documentation' && selectedEmployee && (
                    <DocumentationSection 
                      employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                      darkMode={darkMode} 
                    />
                  )}
                  {!selectedEmployee && (
                    <div className={`p-8 text-center ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
                      <p className="text-lg font-semibold">No employee selected</p>
                      <p className="text-sm mt-2">Please select an employee from the sidebar.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className={`backdrop-blur-lg rounded-3xl shadow-xl border p-12 transition-colors duration-300 ${
                  darkMode
                    ? "bg-gray-800/80 border-gray-700"
                    : "bg-white/80 border-slate-200/50"
                }`}>
                  <div className="text-center py-12">
                    <div className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center ${
                      darkMode
                        ? "bg-gradient-to-br from-indigo-900 to-purple-900"
                        : "bg-gradient-to-br from-indigo-100 to-purple-100"
                    }`}>
                      <Users className={`w-10 h-10 ${
                        darkMode ? "text-indigo-400" : "text-indigo-600"
                      }`} />
                    </div>
                    <p className={`text-xl font-bold mb-2 ${
                      darkMode ? "text-gray-300" : "text-slate-700"
                    }`}>
                      No employees selected
                    </p>
                    <p className={`text-sm ${
                      darkMode ? "text-gray-400" : "text-slate-500"
                    }`}>
                      Select an employee from the sidebar to view their offboarding details
                    </p>
                  </div>
                </div>
              )}

            </main>
          </div>
        )}
      </div>
    </div>
  );
}
