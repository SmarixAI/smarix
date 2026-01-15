'use client';

import { useState, useEffect, useMemo } from 'react';
import { Briefcase, Users, Moon, Sun, User, ArrowLeft, Search, Calendar } from 'lucide-react';

import EmployeeSwitcher from './EmployeeSwitcher';
import Sidebar from './Sidebar';
import FinalCallSection from './managerViewSections/FinalCallSection';
import HandoverSection from './managerViewSections/HandoverSection';
import DocumentationSection from './managerViewSections/DocumentationSection';
import Loader from './Loader';
import { useAuth } from '@/components/auth/AuthContext';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700', '800'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'] });

/* ================= TYPES ================= */

type SectionType = 'finalcall' | 'handover' | 'documentation';
type ViewType = 'dashboard' | 'manage';

type Employee = {
  id: string;
  employeeId?: string;
  name: string;
  role: string;
  designation?: string;
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
  const [allUsersEmployees, setAllUsersEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const [offboardingEmployees, setOffboardingEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [activeSection, setActiveSection] = useState<SectionType>('finalcall');

  /* ================= FETCH LOGIC (Unchanged) ================= */
  const fetchEmployees = async () => {
    try {
      const managerEmployeeId = user?.employeeId;
      
      if (!managerEmployeeId) {
        console.warn('Manager employeeId not found');
        setOffboardingEmployees([]);
        setAllUsersEmployees([]);
        setEmployees([]);
        setLoading(false);
        return;
      }
      
      const empResponse = await fetch('/api/offboarding/employees');
      if (!empResponse.ok) {
        setLoading(false);
        return;
      }
      const empData = await empResponse.json();
      
      const usersResponse = await fetch('/api/users');
      let usersData = { users: [] };
      if (usersResponse.ok) usersData = await usersResponse.json();

      if (empData.employees) {
        setEmployees(empData.employees);
        
        const allEmployeeUsers = usersData.users.filter((u: any) => {
          if (u.role !== 'employee') return false;
          const employeeManagers = u.managers || [];
          return employeeManagers.includes(managerEmployeeId);
        });
        setAllUsersEmployees(allEmployeeUsers);
        
        const offboardUsers = usersData.users.filter((u: any) => {
          const isOffboardEmployee = u.role === 'employee' && u.status === 'offboard';
          if (!isOffboardEmployee) return false;
          const employeeManagers = u.managers || [];
          return employeeManagers.includes(managerEmployeeId);
        });
        
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
            
            if (matchingUser) {
              return { 
                ...emp, 
                employeeId: emp.employeeId || matchingUser.employeeId,
                lastDay: matchingUser.lastDay || emp.lastDay,
                role: matchingUser.designation || emp.role,
                designation: matchingUser.designation || emp.role
              };
            }
            return { ...emp, employeeId: emp.employeeId };
          });
        
        setOffboardingEmployees(offboarding);
        
        if (offboarding.length > 0) {
          setSelectedEmployee(offboarding[0]);
        } else {
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: user.username,
          status: 'offboard',
          lastDay: date,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        alert(`Failed to update employee status: ${errorData.error || 'Unknown error'}`);
        return;
      }

      await fetchEmployees();
      alert('Employee marked as leaving successfully!');
    } catch (error) {
      console.error('Error updating employee status:', error);
      alert('Error updating employee status. Please try again.');
    }
  };

  const filteredEmployees = useMemo(() => {
    let filtered = allUsersEmployees;
    
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
    
    return filtered.sort((a: any, b: any) => {
      const aIsLeaving = a.status === 'offboard';
      const bIsLeaving = b.status === 'offboard';
      if (aIsLeaving && !bIsLeaving) return -1;
      if (!aIsLeaving && bIsLeaving) return 1;
      return 0;
    });
  }, [allUsersEmployees, searchQuery]);

  useEffect(() => {
    if (user?.employeeId) {
      fetchEmployees();
    }
  }, [user]);

  if (loading) {
    return <Loader darkMode={darkMode} message="Loading offboarding data..." fullScreen />;
  }

  return (
    <div className={`min-h-screen pt-0 ${inter.className} ${darkMode ? 'bg-gray-900' : 'bg-slate-50'}`}>

      {/* ================= HEADER ================= */}
      <header className={`sticky top-0 z-50 border-b-2 transition-colors duration-300 backdrop-blur-md ${
        darkMode
          ? "bg-gray-900/80 border-gray-700 shadow-lg"
          : "bg-white/80 border-slate-200 shadow-sm"
      }`}>
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center gap-6">

          {/* LEFT */}
          <div className="flex-1 flex items-center gap-4">
            <div className={`p-2.5 rounded-xl shadow-inner ${
              darkMode ? 'bg-gray-800' : 'bg-gradient-to-br from-slate-100 to-white border border-slate-200'
            }`}>
              <Briefcase className={`w-6 h-6 ${darkMode ? 'text-indigo-400' : 'text-[#0E1B2E]'}`} />
            </div>
            <div>
              <h1 className={`text-xl font-extrabold tracking-tight ${
                darkMode ? "text-white" : "text-[#0E1B2E]"
              }`}>
                Manager Dashboard
              </h1>
              <p className={`text-xs font-medium ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}>
                Offboarding & Knowledge Transfer
              </p>
            </div>
          </div>

          {/* CENTER ACTION */}
          <button
            onClick={() => setView(view === 'dashboard' ? 'manage' : 'dashboard')}
            className={`
              flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold border-2
              transition-all duration-200 shadow-sm
              ${darkMode
                ? "bg-gray-800 border-gray-700 text-gray-200 hover:bg-gray-700"
                : "bg-white border-slate-200 text-[#0E1B2E] hover:bg-slate-50 hover:border-slate-300"
              }
            `}
          >
            <Users className="w-4 h-4" />
            {view === 'dashboard'
              ? 'Manage Staff'
              : 'Return to Dashboard'}
          </button>

          {/* RIGHT */}
          <div className="flex items-center gap-3">
            {setDarkMode && (
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2.5 rounded-xl border-2 transition ${
                  darkMode
                    ? "bg-gray-800 border-gray-700 text-yellow-400 hover:bg-gray-700"
                    : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            )}

            {user && (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className={`p-2.5 rounded-xl border-2 transition flex items-center gap-2 ${
                    darkMode
                      ? "bg-gray-800 border-gray-700 text-gray-200 hover:bg-gray-700"
                      : "bg-white border-slate-200 text-[#0E1B2E] hover:bg-slate-50"
                  }`}
                >
                  <User className="w-5 h-5" />
                  <span className="text-xs font-bold hidden md:inline">{user.name || 'Manager'}</span>
                </button>

                {userMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                    <div className={`absolute right-0 mt-2 w-56 rounded-xl border-2 shadow-xl z-20 overflow-hidden ${
                      darkMode ? "bg-gray-900 border-gray-700" : "bg-white border-slate-200"
                    }`}>
                      <div className={`px-4 py-3 border-b-2 ${darkMode ? "border-gray-800" : "border-slate-100"}`}>
                        <p className={`text-sm font-bold ${darkMode ? "text-white" : "text-[#0E1B2E]"}`}>
                          {user.name || user.username}
                        </p>
                        <p className={`text-xs ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
                          Manager Access
                        </p>
                      </div>
                      <div className="p-2">
                        <button
                          onClick={() => {
                            setUserMenuOpen(false);
                            logout();
                          }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
                            darkMode
                              ? "hover:bg-gray-800 text-gray-300"
                              : "hover:bg-slate-50 text-red-600"
                          }`}
                        >
                          <ArrowLeft className="w-4 h-4" />
                          Sign Out
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
          <div className={`rounded-2xl shadow-lg p-8 space-y-6 border-2 backdrop-blur-sm ${
            darkMode
              ? "bg-gray-800/50 border-gray-700"
              : "bg-white/70 border-slate-200"
          }`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className={`text-2xl font-bold ${darkMode ? "text-white" : "text-[#0E1B2E]"}`}>
                  Manage Employees
                </h2>
                <p className={`text-sm mt-1 ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                  Initiate offboarding or view status
                </p>
              </div>
            </div>

            {/* Search Bar */}
            <div className="relative">
              <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 ${
                darkMode ? "text-gray-500" : "text-slate-400"
              }`} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name, ID, or role..."
                className={`w-full pl-12 pr-4 py-3 rounded-xl border-2 outline-none transition-colors font-medium ${
                  darkMode
                    ? "bg-gray-900/50 text-white border-gray-700 focus:border-indigo-500"
                    : "bg-white text-[#0E1B2E] border-slate-200 focus:border-blue-400 placeholder:text-slate-400"
                }`}
              />
            </div>

            <div className="grid gap-4">
              {filteredEmployees.length === 0 ? (
                <div className={`text-center py-16 rounded-2xl border-2 border-dashed ${
                  darkMode ? "border-gray-700 text-gray-500" : "border-slate-200 text-slate-400"
                }`}>
                  <p className="font-medium">No employees found matching your search</p>
                </div>
              ) : (
                filteredEmployees.map((user: any) => {
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
                        flex items-center justify-between rounded-xl p-5 border-2 transition-all
                        ${darkMode
                          ? "border-gray-700 bg-gray-800/40 hover:bg-gray-800"
                          : "border-slate-200 bg-white hover:bg-slate-50 shadow-sm hover:shadow-md"
                        }
                      `}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg border-2 ${
                          darkMode 
                           ? "bg-gray-700 border-gray-600 text-white" 
                           : "bg-slate-50 border-slate-200 text-[#0E1B2E]"
                        }`}>
                          {displayName.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p className={`font-bold text-lg ${
                            darkMode ? "text-gray-100" : "text-[#0E1B2E]"
                          }`}>
                            {displayName}
                          </p>
                          <div className="flex items-center gap-2">
                            <p className={`text-sm font-medium ${
                              darkMode ? "text-gray-400" : "text-slate-600"
                            }`}>
                              {displayRole}
                            </p>
                            {user.employeeId && (
                              <span className={`text-xs px-2 py-0.5 rounded border ${
                                darkMode ? "bg-gray-800 border-gray-700 text-gray-500" : "bg-slate-100 border-slate-200 text-slate-500"
                              }`}>
                                {user.employeeId}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {isOffboarding ? (
                        <div className={`px-4 py-2 rounded-xl border-2 flex items-center gap-2 ${
                          darkMode
                            ? "bg-red-900/20 border-red-900 text-red-300"
                            : "bg-amber-50 border-amber-200 text-amber-800"
                        }`}>
                          <Calendar className="w-4 h-4" />
                          <span className="text-sm font-bold">
                            {user.lastDay && user.lastDay !== 'null'
                              ? `Leaving: ${user.lastDay}`
                              : 'Offboarding Active'}
                          </span>
                        </div>
                      ) : (
                        <div className="flex gap-3 items-center">
                          <input
                            type="date"
                            data-username={user.username}
                            className={`
                              border-2 rounded-xl px-4 py-2.5 text-sm outline-none transition-all
                              ${darkMode
                                ? "border-gray-600 bg-gray-900 text-white focus:border-indigo-500"
                                : "border-slate-200 bg-white text-[#0E1B2E] focus:border-blue-500"
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
                              px-5 py-2.5 rounded-xl text-white text-sm font-semibold shadow-md
                              transition-all hover:shadow-lg active:scale-95
                              bg-gradient-to-r from-[#0E1B2E] to-blue-900
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
          <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">

            {/* SIDEBAR */}
            <aside className="col-span-3 h-full flex flex-col gap-6">
              <div className="flex-1 overflow-y-auto">
              {offboardingEmployees.length > 0 ? (
                <EmployeeSwitcher
                  employees={offboardingEmployees}
                  selected={selectedEmployee}
                  onSelect={setSelectedEmployee}
                  darkMode={darkMode}
                />
              ) : (
                <div className={`rounded-2xl border-2 p-6 text-center h-full flex flex-col items-center justify-center ${
                  darkMode ? "bg-gray-800/50 border-gray-700" : "bg-white/70 border-slate-200"
                }`}>
                  <div className={`p-4 rounded-full mb-4 ${
                    darkMode ? "bg-gray-700 text-gray-400" : "bg-slate-100 text-slate-400"
                  }`}>
                    <Users className="w-8 h-8" />
                  </div>
                  <h3 className={`font-bold ${darkMode ? "text-white" : "text-[#0E1B2E]"}`}>
                    No Active Offboardings
                  </h3>
                  <p className={`text-xs mt-2 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
                    Use "Manage Staff" to initiate exit.
                  </p>
                </div>
              )}
              </div>

              {selectedEmployee && (
                <div className="shrink-0">
                  <Sidebar
                    activeSection={activeSection}
                    onChangeSection={setActiveSection}
                    selectedEmployee={selectedEmployee}
                    darkMode={darkMode}
                  />
                </div>
              )}
            </aside>

            {/* MAIN */}
            <main className="col-span-9 h-full flex flex-col gap-4">

              {/* TABS */}
              <div className={`rounded-2xl border-2 p-1.5 backdrop-blur-sm ${
                darkMode
                  ? "bg-gray-800/80 border-gray-700"
                  : "bg-white/80 border-slate-200"
              }`}>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { key: 'finalcall', label: 'Final Call' },
                    { key: 'handover', label: 'Task Handover' },
                    { key: 'documentation', label: 'Documentation' }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveSection(tab.key as SectionType)}
                      className={`
                        py-2.5 rounded-xl text-sm font-bold transition-all duration-200
                        ${activeSection === tab.key
                            ? 'bg-gradient-to-r from-[#0E1B2E] to-blue-900 text-white shadow-md'
                            : darkMode
                              ? 'text-gray-400 hover:text-white hover:bg-gray-700'
                              : 'text-slate-500 hover:text-[#0E1B2E] hover:bg-slate-50'
                        }
                      `}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* CONTENT AREA */}
              <div className="flex-1 overflow-hidden">
                {selectedEmployee ? (
                  <div className="h-full animate-fadeIn">
                    {activeSection === 'finalcall' && (
                      <FinalCallSection 
                        employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                        darkMode={darkMode} 
                      />
                    )}
                    {activeSection === 'handover' && (
                      <HandoverSection 
                        employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                        darkMode={darkMode} 
                      />
                    )}
                    {activeSection === 'documentation' && (
                      <DocumentationSection 
                        employeeId={selectedEmployee.employeeId || selectedEmployee.id || ''} 
                        darkMode={darkMode} 
                      />
                    )}
                  </div>
                ) : (
                  <div className={`h-full rounded-2xl border-2 flex items-center justify-center ${
                    darkMode
                      ? "bg-gray-800/30 border-gray-700"
                      : "bg-white/50 border-slate-200 border-dashed"
                  }`}>
                    <div className="text-center p-8">
                      <p className={`text-lg font-bold ${darkMode ? "text-gray-300" : "text-[#0E1B2E]"}`}>
                        Select an employee
                      </p>
                      <p className={`text-sm ${darkMode ? "text-gray-500" : "text-slate-500"}`}>
                        Choose from the sidebar to view details
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </main>
          </div>
        )}
      </div>
    </div>
  );
}