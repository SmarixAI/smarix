'use client';

import { useState, useEffect, useMemo } from 'react';
import { 
  Users, Moon, Sun, User, LogOut, Search, ChevronDown, ChevronUp,
  Clock, CheckCircle, TrendingUp, MessageSquare
} from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';
import { PieChart, Pie, Cell, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Line } from 'recharts';
import Loader from '../offboarding/Loader';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Employee = {
  id: string;
  employeeId: string;
  name: string;
  role: string;
  username: string;
  status: 'onboard' | 'offboard';
  profilePicture?: string;
};

type SectionProgress = {
  section: string;
  status: 'Pending' | 'Completed';
  expectedHours: number;
  spentHours: number | null;
  completion: number;
  value?: number;
};

type EmployeeProgress = {
  employeeId: string;
  employeeName: string;
  type: 'onboarding' | 'offboarding';
  pendingSections: number;
  completedSections: number;
  efficiency: number;
  overallProgress: number;
  sections: SectionProgress[];
  timeSpentData: { section: string; expected: number; spent: number }[];
};

export default function UnifiedDashboard({ darkMode = false, setDarkMode }: { darkMode?: boolean; setDarkMode?: (value: boolean) => void }) {
  const { user, logout, token } = useAuth();
  const [onboardingEmployees, setOnboardingEmployees] = useState<Employee[]>([]);
  const [offboardingEmployees, setOffboardingEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [employeeProgress, setEmployeeProgress] = useState<EmployeeProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [onboardingExpanded, setOnboardingExpanded] = useState(true);
  const [offboardingExpanded, setOffboardingExpanded] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Initial render log
  useEffect(() => {
    console.log('🚀 UnifiedDashboard component mounted/rendered');
    console.log('Initial user:', user);
    console.log('Initial token:', token ? 'exists' : 'missing');
  }, []);

  // Fetch employees
  useEffect(() => {
    console.log('=== UnifiedDashboard useEffect triggered ===');
    console.log('User object:', user);
    console.log('Token exists:', !!token);
    
    const fetchEmployees = async () => {
      try {
        console.log('=== Starting fetchEmployees ===');
        
        // Get manager's employeeId - try both employeeId and employee_id (if present)
        const managerId = user?.employeeId || (user as any)?.employee_id;
        
        console.log('Manager ID extracted:', managerId);
        console.log('Full user object:', JSON.stringify(user, null, 2));
        
        if (!managerId || !token) {
          console.error('❌ Missing managerId or token:', { 
            managerId, 
            hasToken: !!token, 
            user,
            employeeId: user?.employeeId,
            employee_id: (user as any)?.employee_id
          });
          setLoading(false);
          return;
        }

        console.log('✅ Fetching employees for manager:', managerId);
        console.log('API URL:', `${API_URL}/auth/users`);

        const response = await fetch(`${API_URL}/auth/users`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ Failed to fetch users:', response.status, errorText);
          setLoading(false);
          return;
        }

        const allUsers = await response.json();
        console.log('=== DEBUG: Employee Filtering ===');
        console.log('All users from API:', allUsers.length);
        console.log('Manager ID:', managerId);
        console.log('Manager user object:', JSON.stringify(user, null, 2));
        
        // Log all employee users to see their structure
        const allEmployees = allUsers.filter((u: any) => (u.role || '').toLowerCase() === 'employee');
        console.log('Total employees found:', allEmployees.length);
        console.log('All employees:', allEmployees.map((u: any) => ({
          username: u.username,
          status: u.status,
          employeeId: u.employeeId || u.employee_id,
          managers: u.managers,
          name: u.name
        })));

        // Filter employees managed by this manager
        const filtered = allUsers.filter((u: any) => {
          const role = (u.role || '').toLowerCase();
          const managers = u.managers || [];
          
          // Get employee's employeeId (backend uses employee_id, but check both)
          const employeeId = u.employee_id || u.employeeId;
          
          const isEmployee = role === "employee";
          
          // Check if manager's ID is in the employee's managers array
          // Also handle case where managers might be stored as strings or IDs
          const isManagedByMe = Array.isArray(managers) && (
            managers.includes(managerId) || 
            managers.some((m: any) => String(m) === String(managerId))
          );
          
          if (isEmployee) {
            console.log(`Employee ${u.username || 'unknown'}:`, {
              role,
              status: u.status,
              employeeId,
              managers,
              'managersArray': JSON.stringify(managers),
              'managersTypes': managers.map((m: any) => typeof m),
              isManagedByMe,
              managerId,
              'managerIdType': typeof managerId,
              'directInclude': managers.includes(managerId),
              'stringCompare': managers.some((m: any) => String(m) === String(managerId)),
              'statusType': typeof u.status,
              'statusLower': (u.status || '').toLowerCase()
            });
          }
          
          return isEmployee && isManagedByMe;
        });

        console.log('Filtered employees (by manager):', filtered.length);
        console.log('Filtered employees list:', filtered.map((u: any) => ({
          username: u.username,
          status: u.status,
          name: u.name
        })));

        // Separate onboarding and offboarding employees
        console.log('=== STATUS CHECKING ===');
        filtered.forEach((u: any) => {
          const rawStatus = u.status;
          const normalizedStatus = (rawStatus || '').toLowerCase().trim();
          console.log(`Employee ${u.username}: rawStatus="${rawStatus}" (type: ${typeof rawStatus}), normalized="${normalizedStatus}"`);
        });

        const onboarding = filtered
          .filter((u: any) => {
            const status = (u.status || '').toLowerCase().trim();
            const result = status === 'onboard';
            if (result) {
              console.log(`✓ Onboarding: ${u.username} - status: "${u.status}" (normalized: "${status}")`);
            }
            return result;
          })
          .map((u: any) => {
            const employeeId = u.employee_id || u.employeeId || u.username;
            return {
              id: employeeId,
              employeeId: employeeId,
              name: u.name || u.username,
              role: u.designation || u.role || 'Employee',
              username: u.username,
              status: 'onboard' as const,
              profilePicture: u.profilePicture,
            };
          });

        const offboarding = filtered
          .filter((u: any) => {
            const rawStatus = u.status;
            const status = (rawStatus || '').toLowerCase().trim();
            
            // Check multiple possible values for offboarding status
            const isOffboarding = status === 'offboard' || 
                                 status === 'offboarding' || 
                                 status === 'off-boarding' ||
                                 status === 'leaving' ||
                                 (status && status.includes('offboard'));
            
            console.log(`🔍 Checking offboarding for ${u.username || 'unknown'}:`);
            console.log(`   - Raw status: "${rawStatus}" (type: ${typeof rawStatus})`);
            console.log(`   - Normalized: "${status}"`);
            console.log(`   - Match "offboard": ${status === 'offboard'}`);
            console.log(`   - Is offboarding (flexible): ${isOffboarding}`);
            console.log(`   - Full user object:`, JSON.stringify(u, null, 2));
            
            if (!isOffboarding && rawStatus) {
              console.warn(`   ⚠️ Status "${rawStatus}" does not match offboarding criteria`);
            }
            
            return isOffboarding;
          })
          .map((u: any) => {
            const employeeId = u.employee_id || u.employeeId || u.username;
            console.log(`✓ Mapping offboarding employee: ${u.username} -> ${employeeId}`);
            return {
              id: employeeId,
              employeeId: employeeId,
              name: u.name || u.username,
              role: u.designation || u.role || 'Employee',
              username: u.username,
              status: 'offboard' as const,
              profilePicture: u.profilePicture,
            };
          });

        console.log('=== RESULTS ===');
        console.log('Onboarding employees:', onboarding.length, onboarding);
        console.log('Offboarding employees:', offboarding.length, offboarding);
        
        // Debug: Check what statuses we actually have
        console.log('All statuses in filtered employees:', filtered.map((u: any) => ({
          username: u.username,
          status: u.status,
          statusType: typeof u.status
        })));

        setOnboardingEmployees(onboarding);
        setOffboardingEmployees(offboarding);
        setLoading(false);
        console.log('✅ Final state - Onboarding:', onboarding.length, 'Offboarding:', offboarding.length);
      } catch (error) {
        console.error('❌ ERROR in fetchEmployees:', error);
        console.error('Error details:', error instanceof Error ? error.message : String(error));
        console.error('Error stack:', error instanceof Error ? error.stack : 'No stack');
        setLoading(false);
      }
    };

    // Only fetch if we have user and token
    if (user && token) {
      console.log('🔍 Calling fetchEmployees...');
      fetchEmployees().catch((error) => {
        console.error('❌ Unhandled error in fetchEmployees:', error);
      });
    } else {
      console.log('⏸️ Skipping fetchEmployees - missing user or token', { user: !!user, token: !!token });
      setLoading(false);
    }
  }, [user, token]);

  // Generate dummy progress data when employee is selected
  useEffect(() => {
    if (!selectedEmployee) {
      setEmployeeProgress(null);
      return;
    }

    // Generate dummy progress data
    const isOnboarding = selectedEmployee.status === 'onboard';
    const sections = isOnboarding
      ? ['Overview', 'Q&A', 'Practice', 'Bug Fixing', 'Handover']
      : ['Final Call', 'Handover', 'Documentation'];

    const dummySections: SectionProgress[] = sections.map((section, idx) => {
      const expected = [5, 4, 3.5, 5.5, 4.5][idx] || 4;
      const spent = idx === 0 ? 4.3 : idx === 1 ? null : idx === 2 ? 2.8 : idx === 3 ? 8.2 : 4.5;
      const completion = spent ? Math.round((spent / expected) * 100) : 0;
      const status = idx < 2 ? 'Pending' : 'Completed';
      
      return {
        section,
        status: status as 'Pending' | 'Completed',
        expectedHours: expected,
        spentHours: spent,
        completion: completion > 100 ? 149 : completion,
        value: spent ? Math.round(spent * 10) : undefined,
      };
    });

    const completed = dummySections.filter(s => s.status === 'Completed').length;
    const pending = dummySections.filter(s => s.status === 'Pending').length;
    const overallProgress = Math.round((completed / sections.length) * 100);
    const efficiency = Math.round(85 + Math.random() * 10);

    const timeSpentData = dummySections
      .filter(s => s.spentHours !== null)
      .map(s => ({
        section: s.section,
        expected: s.expectedHours,
        spent: s.spentHours || 0,
      }));

    setEmployeeProgress({
      employeeId: selectedEmployee.employeeId,
      employeeName: selectedEmployee.name,
      type: isOnboarding ? 'onboarding' : 'offboarding',
      pendingSections: pending,
      completedSections: completed,
      efficiency,
      overallProgress,
      sections: dummySections,
      timeSpentData,
    });
  }, [selectedEmployee]);

  // Filter employees based on search
  const filteredOnboarding = useMemo(() => {
    if (!searchQuery) return onboardingEmployees;
    const query = searchQuery.toLowerCase();
    return onboardingEmployees.filter(emp =>
      emp.name.toLowerCase().includes(query) ||
      emp.role.toLowerCase().includes(query) ||
      emp.username.toLowerCase().includes(query)
    );
  }, [onboardingEmployees, searchQuery]);

  const filteredOffboarding = useMemo(() => {
    if (!searchQuery) return offboardingEmployees;
    const query = searchQuery.toLowerCase();
    return offboardingEmployees.filter(emp =>
      emp.name.toLowerCase().includes(query) ||
      emp.role.toLowerCase().includes(query) ||
      emp.username.toLowerCase().includes(query)
    );
  }, [offboardingEmployees, searchQuery]);

  // Chart colors
  const COLORS = {
    pending: darkMode ? '#f97316' : '#fb923c',
    completed: darkMode ? '#10b981' : '#34d399',
    efficiency: darkMode ? '#8b5cf6' : '#a78bfa',
    donut: {
      pending: darkMode ? '#f97316' : '#fb923c',
      completed: darkMode ? '#10b981' : '#34d399',
    },
  };

  // Log component state
  console.log('📊 UnifiedDashboard render - State:', {
    loading,
    onboardingCount: onboardingEmployees.length,
    offboardingCount: offboardingEmployees.length,
    hasUser: !!user,
    hasToken: !!token,
    selectedEmployee: selectedEmployee?.name || 'none'
  });

  if (loading) {
    console.log('⏳ Showing loader...');
    return <Loader darkMode={darkMode} message="Loading dashboard..." fullScreen />;
  }

  console.log('✅ Rendering dashboard content');

  // Donut chart data
  const donutData = employeeProgress
    ? [
        { name: 'Pending', value: 100 - employeeProgress.overallProgress, fill: COLORS.donut.pending },
        { name: 'Completed', value: employeeProgress.overallProgress, fill: COLORS.donut.completed },
      ]
    : [];

  return (
    <div className={`min-h-screen flex transition-colors duration-300 ${
      darkMode ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      {/* SIDEBAR */}
      <div className={`w-80 border-r transition-colors duration-300 ${
        darkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
      }`}>
        <div className="p-4 border-b" style={{ borderColor: darkMode ? '#374151' : '#e5e7eb' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-lg ${
              darkMode ? 'bg-indigo-900/30' : 'bg-indigo-100'
            }`}>
              <span className={`text-lg font-bold ${
                darkMode ? 'text-indigo-400' : 'text-indigo-600'
              }`}>
                S
              </span>
            </div>
            <h2 className={`text-lg font-bold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Smarix
            </h2>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`} />
            <input
              type="text"
              placeholder="Q Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 rounded-lg border transition-colors ${
                darkMode
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>
        </div>

        <div className="overflow-y-auto" style={{ height: 'calc(100vh - 120px)' }}>
          {/* Onboarding Section */}
          <div>
            <button
              onClick={() => setOnboardingExpanded(!onboardingExpanded)}
              className={`w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-50 transition-colors ${
                darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
              }`}
            >
              <span className={`font-semibold ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Onboarding
              </span>
              {onboardingExpanded ? (
                <ChevronUp className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              ) : (
                <ChevronDown className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              )}
            </button>
            
            {onboardingExpanded && (
              <div>
                {filteredOnboarding.length === 0 ? (
                  <div className={`px-4 py-8 text-center ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    No onboarding employees found
                  </div>
                ) : (
                  filteredOnboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`px-4 py-3 flex items-center gap-3 cursor-pointer transition-colors ${
                        selectedEmployee?.id === emp.id
                          ? darkMode
                            ? 'bg-indigo-900/30 border-l-4 border-indigo-500'
                            : 'bg-indigo-50 border-l-4 border-indigo-500'
                          : darkMode
                          ? 'hover:bg-gray-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        darkMode ? 'bg-gray-700' : 'bg-gray-200'
                      }`}>
                        {emp.profilePicture ? (
                          <img src={emp.profilePicture} alt={emp.name} className="w-full h-full rounded-full" />
                        ) : (
                          <User className={`w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`font-medium truncate ${
                          darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {emp.name}
                        </div>
                        <div className={`text-xs truncate ${
                          darkMode ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          {emp.role}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Offboarding Section */}
          <div className="border-t" style={{ borderColor: darkMode ? '#374151' : '#e5e7eb' }}>
            <button
              onClick={() => setOffboardingExpanded(!offboardingExpanded)}
              className={`w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-50 transition-colors ${
                darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
              }`}
            >
              <span className={`font-semibold ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Offboarding
              </span>
              {offboardingExpanded ? (
                <ChevronUp className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              ) : (
                <ChevronDown className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              )}
            </button>
            
            {offboardingExpanded && (
              <div>
                {filteredOffboarding.length === 0 ? (
                  <div className={`px-4 py-8 text-center ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    No offboarding employees found
                  </div>
                ) : (
                  filteredOffboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`px-4 py-3 flex items-center gap-3 cursor-pointer transition-colors ${
                        selectedEmployee?.id === emp.id
                          ? darkMode
                            ? 'bg-indigo-900/30 border-l-4 border-indigo-500'
                            : 'bg-indigo-50 border-l-4 border-indigo-500'
                          : darkMode
                          ? 'hover:bg-gray-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        darkMode ? 'bg-gray-700' : 'bg-gray-200'
                      }`}>
                        {emp.profilePicture ? (
                          <img src={emp.profilePicture} alt={emp.name} className="w-full h-full rounded-full" />
                        ) : (
                          <User className={`w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`font-medium truncate ${
                          darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {emp.name}
                        </div>
                        <div className={`text-xs truncate ${
                          darkMode ? 'text-gray-400' : 'text-gray-500'
                        }`}>
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

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col">
        {/* HEADER */}
        <header className={`border-b transition-colors duration-300 ${
          darkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
        }`}>
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Welcome back
              </p>
              <h1 className={`text-2xl font-bold ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Onboarding / Offboarding Dashboard
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => setDarkMode?.(!darkMode)}
                className={`p-2 rounded-lg transition-colors ${
                  darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                }`}
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-gray-600" />}
              </button>
              
              {user && (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2"
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      darkMode ? 'bg-indigo-600' : 'bg-indigo-100'
                    }`}>
                      <User className={`w-4 h-4 ${darkMode ? 'text-white' : 'text-indigo-600'}`} />
                    </div>
                  </button>
                  
                  {userMenuOpen && (
                    <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-lg border z-50 ${
                      darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                    }`}>
                      <button
                        onClick={logout}
                        className={`w-full px-4 py-2 text-left flex items-center gap-2 rounded-lg transition-colors ${
                          darkMode ? 'hover:bg-gray-700 text-red-400' : 'hover:bg-gray-100 text-red-600'
                        }`}
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* DASHBOARD CONTENT */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedEmployee ? (
            <div className={`text-center py-20 rounded-2xl ${
              darkMode ? 'bg-gray-800' : 'bg-white'
            }`}>
              <Users className={`w-16 h-16 mx-auto mb-4 ${
                darkMode ? 'text-gray-600' : 'text-gray-400'
              }`} />
              <h3 className={`text-xl font-semibold mb-2 ${
                darkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Select an employee to view progress
              </h3>
              <p className={`${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                Choose an employee from the sidebar to see their onboarding or offboarding progress
              </p>
            </div>
          ) : employeeProgress ? (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className={`p-6 rounded-2xl border ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-3 rounded-lg ${
                      darkMode ? 'bg-orange-900/30' : 'bg-orange-100'
                    }`}>
                      <Clock className={`w-6 h-6 ${
                        darkMode ? 'text-orange-400' : 'text-orange-600'
                      }`} />
                    </div>
                    <div>
                      <p className={`text-sm ${
                        darkMode ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Pending
                      </p>
                      <p className={`text-2xl font-bold ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        {employeeProgress.pendingSections} sections
                      </p>
                    </div>
                  </div>
                </div>

                <div className={`p-6 rounded-2xl border ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-3 rounded-lg ${
                      darkMode ? 'bg-green-900/30' : 'bg-green-100'
                    }`}>
                      <CheckCircle className={`w-6 h-6 ${
                        darkMode ? 'text-green-400' : 'text-green-600'
                      }`} />
                    </div>
                    <div>
                      <p className={`text-sm ${
                        darkMode ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Completed
                      </p>
                      <p className={`text-2xl font-bold ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        {employeeProgress.completedSections} sections
                      </p>
                    </div>
                  </div>
                </div>

                <div className={`p-6 rounded-2xl border ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-3 rounded-lg ${
                      darkMode ? 'bg-purple-900/30' : 'bg-purple-100'
                    }`}>
                      <TrendingUp className={`w-6 h-6 ${
                        darkMode ? 'text-purple-400' : 'text-purple-600'
                      }`} />
                    </div>
                    <div>
                      <p className={`text-sm ${
                        darkMode ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Efficiency
                      </p>
                      <p className={`text-2xl font-bold ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        {employeeProgress.efficiency}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Donut Chart */}
                <div className={`p-6 rounded-2xl border ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <h3 className={`text-lg font-semibold mb-4 ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    {employeeProgress.employeeName} Progress
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={donutData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {donutData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                          border: darkMode ? '1px solid #374151' : '1px solid #e5e7eb',
                          borderRadius: '8px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        darkMode ? 'bg-orange-400' : 'bg-orange-500'
                      }`} />
                      <span className={`text-sm ${
                        darkMode ? 'text-gray-300' : 'text-gray-700'
                      }`}>
                        Pending: {100 - employeeProgress.overallProgress}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        darkMode ? 'bg-green-400' : 'bg-green-500'
                      }`} />
                      <span className={`text-sm ${
                        darkMode ? 'text-gray-300' : 'text-gray-700'
                      }`}>
                        Completed: {employeeProgress.overallProgress}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Time Spent vs Expected Chart */}
                <div className={`p-6 rounded-2xl border ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <h3 className={`text-lg font-semibold mb-4 ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    Time Spent vs. Expected
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <ComposedChart data={employeeProgress.timeSpentData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
                      <XAxis
                        dataKey="section"
                        stroke={darkMode ? '#9ca3af' : '#6b7280'}
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis
                        stroke={darkMode ? '#9ca3af' : '#6b7280'}
                        style={{ fontSize: '12px' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                          border: darkMode ? '1px solid #374151' : '1px solid #e5e7eb',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Bar dataKey="expected" fill={darkMode ? '#3b82f6' : '#60a5fa'} name="Expected (h)" />
                      <Line type="monotone" dataKey="spent" stroke={darkMode ? '#10b981' : '#34d399'} strokeWidth={2} name="Time spent (h)" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Section Progress Table */}
              <div className={`p-6 rounded-2xl border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <h3 className={`text-lg font-semibold mb-4 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Section Progress
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className={`border-b ${
                        darkMode ? 'border-gray-700' : 'border-gray-200'
                      }`}>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Section
                        </th>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Status
                        </th>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Expected (h)
                        </th>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Spent (h)
                        </th>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Completion
                        </th>
                        <th className={`text-left py-3 px-4 text-sm font-semibold ${
                          darkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          Completion
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {employeeProgress.sections.map((section, idx) => (
                        <tr
                          key={idx}
                          className={`border-b transition-colors ${
                            darkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          <td className={`py-3 px-4 font-medium ${
                            darkMode ? 'text-white' : 'text-gray-900'
                          }`}>
                            {section.section}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              section.status === 'Completed'
                                ? darkMode
                                  ? 'bg-green-900/30 text-green-400'
                                  : 'bg-green-100 text-green-700'
                                : darkMode
                                ? 'bg-orange-900/30 text-orange-400'
                                : 'bg-orange-100 text-orange-700'
                            }`}>
                              {section.status}
                            </span>
                          </td>
                          <td className={`py-3 px-4 ${
                            darkMode ? 'text-gray-300' : 'text-gray-700'
                          }`}>
                            {section.expectedHours} h
                          </td>
                          <td className={`py-3 px-4 ${
                            darkMode ? 'text-gray-300' : 'text-gray-700'
                          }`}>
                            {section.spentHours !== null ? `${section.spentHours} h` : '-'}
                          </td>
                          <td className="py-3 px-4">
                            <div className="w-32 h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                              <div
                                className={`h-full ${
                                  section.completion > 100
                                    ? 'bg-red-500'
                                    : section.status === 'Completed'
                                    ? darkMode
                                      ? 'bg-green-500'
                                      : 'bg-green-400'
                                    : darkMode
                                    ? 'bg-blue-500'
                                    : 'bg-blue-400'
                                }`}
                                style={{
                                  width: `${Math.min(section.completion, 100)}%`,
                                }}
                              />
                            </div>
                          </td>
                          <td className={`py-3 px-4 ${
                            darkMode ? 'text-gray-300' : 'text-gray-700'
                          }`}>
                            {section.spentHours !== null
                              ? section.completion > 100
                                ? `${section.completion}%`
                                : `${section.completion}%`
                              : 'Not started'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <Loader darkMode={darkMode} message="Loading progress..." />
          )}
        </div>
      </div>
    </div>
  );
}

