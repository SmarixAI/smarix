'use client';

import { useState, useEffect, useMemo } from 'react';
import { 
  Users, User, LogOut, Search, ChevronDown, ChevronUp,
  Clock, CheckCircle, TrendingUp
} from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';
import { PieChart, Pie, Cell, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Line } from 'recharts';
import Loader from '../offboarding/Loader';
import Image from 'next/image';

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

export default function UnifiedDashboard() {
  const { user, logout, token } = useAuth();
  const [onboardingEmployees, setOnboardingEmployees] = useState<Employee[]>([]);
  const [offboardingEmployees, setOffboardingEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [employeeProgress, setEmployeeProgress] = useState<EmployeeProgress | null>(null);
  const [loading, setLoading] = useState(true);
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
      ? ['Overview', 'Q&A', 'Practice', 'Bug Fixing']
      : ['Final Call', 'Handover', 'Documentation'];

    const dummySections: SectionProgress[] = sections.map((section, idx) => {
      const expected = [5, 4, 3.5, 5.5][idx] || 4;
      const spent = idx === 0 ? 4.3 : idx === 1 ? 3.2 : idx === 2 ? 2.8 : idx === 3 ? 4.1 : 0;
      const completion = spent ? Math.round((spent / expected) * 100) : 0;
      const status = idx < 2 ? 'Pending' : idx === 3 ? 'Pending' : 'Completed';
      
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
    pending: '#fb923c',
    completed: '#34d399',
    efficiency: '#a78bfa',
    donut: {
      pending: '#fb923c',
      completed: '#34d399',
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
    return <Loader darkMode={false} message="Loading dashboard..." fullScreen />;
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
    <div className="min-h-screen flex bg-[#FAFAFA]">
      {/* SIDEBAR */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-screen">
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
            Manager Dashboard
          </p>
        </div>

        {/* Profile & Logout */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {user && (
              <>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-[#0E1B2E] truncate">
                    {user.name || user.username}
                  </div>
                  <div className="text-xs text-[#0E1B2E]/60 capitalize truncate">
                    {user.role || 'Manager'}
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
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border bg-white border-gray-300 text-[#0E1B2E] placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/20 focus:border-[#0E1B2E]"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Onboarding Section */}
          <div>
            <button
              onClick={() => setOnboardingExpanded(!onboardingExpanded)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#0E1B2E]/5 transition-colors"
            >
              <span className="font-semibold text-[#0E1B2E]">
                Onboarding
              </span>
              {onboardingExpanded ? (
                <ChevronUp className="w-4 h-4 text-[#0E1B2E]/60" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#0E1B2E]/60" />
              )}
            </button>
            
            {onboardingExpanded && (
              <div>
                {filteredOnboarding.length === 0 ? (
                  <div className="px-4 py-8 text-center text-[#0E1B2E]/60">
                    No onboarding employees found
                  </div>
                ) : (
                  filteredOnboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`px-4 py-3 flex items-center gap-3 cursor-pointer transition-colors ${
                        selectedEmployee?.id === emp.id
                          ? 'bg-[#0E1B2E]/5 border-l-4 border-[#0E1B2E]'
                          : 'hover:bg-[#0E1B2E]/5'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-200">
                        {emp.profilePicture ? (
                          <img src={emp.profilePicture} alt={emp.name} className="w-full h-full rounded-full" />
                        ) : (
                          <User className="w-5 h-5 text-[#0E1B2E]/60" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate text-[#0E1B2E]">
                          {emp.name}
                        </div>
                        <div className="text-xs truncate text-[#0E1B2E]/60">
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
          <div className="border-t border-gray-200">
            <button
              onClick={() => setOffboardingExpanded(!offboardingExpanded)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#0E1B2E]/5 transition-colors"
            >
              <span className="font-semibold text-[#0E1B2E]">
                Offboarding
              </span>
              {offboardingExpanded ? (
                <ChevronUp className="w-4 h-4 text-[#0E1B2E]/60" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#0E1B2E]/60" />
              )}
            </button>
            
            {offboardingExpanded && (
              <div>
                {filteredOffboarding.length === 0 ? (
                  <div className="px-4 py-8 text-center text-[#0E1B2E]/60">
                    No offboarding employees found
                  </div>
                ) : (
                  filteredOffboarding.map((emp) => (
                    <div
                      key={emp.id}
                      onClick={() => setSelectedEmployee(emp)}
                      className={`px-4 py-3 flex items-center gap-3 cursor-pointer transition-colors ${
                        selectedEmployee?.id === emp.id
                          ? 'bg-[#0E1B2E]/5 border-l-4 border-[#0E1B2E]'
                          : 'hover:bg-[#0E1B2E]/5'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-200">
                        {emp.profilePicture ? (
                          <img src={emp.profilePicture} alt={emp.name} className="w-full h-full rounded-full" />
                        ) : (
                          <User className="w-5 h-5 text-[#0E1B2E]/60" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate text-[#0E1B2E]">
                          {emp.name}
                        </div>
                        <div className="text-xs truncate text-[#0E1B2E]/60">
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
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* DASHBOARD CONTENT */}
        <div className="flex-1 overflow-y-auto p-6 relative">
          {/* Grid Pattern Background - matching landing page */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
          
          {!selectedEmployee ? (
            <div className="text-center py-20 rounded-xl relative z-10 bg-white border border-gray-200">
              <Users className="w-16 h-16 mx-auto mb-4 text-[#0E1B2E]/20" />
              <h3 className="text-xl font-semibold mb-2 text-[#0E1B2E]">
                Select an employee to view progress
              </h3>
              <p className="text-[#0E1B2E]/60">
                Choose an employee from the sidebar to see their onboarding or offboarding progress
              </p>
            </div>
          ) : employeeProgress ? (
            <div className="space-y-3 relative z-10">
              {/* Employee Info Section */}
              {selectedEmployee?.status === 'offboard' && (
                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60 mb-1">
                        Last Working Day
                      </p>
                      <p className="text-sm font-semibold text-[#0E1B2E]">
                        2026-01-26
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60 mb-1">
                        Effective Workdays
                      </p>
                      <p className="text-sm font-semibold text-[#0E1B2E]">
                        10 Days
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60 mb-1">
                        High-Risk Tasks
                      </p>
                      <p className="text-sm font-semibold text-[#0E1B2E]">
                        0 Tasks
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Summary Cards - Compact */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-orange-100">
                      <Clock className="w-5 h-5 text-orange-600" />
                    </div>
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60">
                        Pending
                      </p>
                      <p className="text-xl font-bold text-[#0E1B2E]">
                        {employeeProgress.pendingSections} sections
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-green-100">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60">
                        Completed
                      </p>
                      <p className="text-xl font-bold text-[#0E1B2E]">
                        {employeeProgress.completedSections} sections
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-purple-100">
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-xs text-[#0E1B2E]/60">
                        Efficiency
                      </p>
                      <p className="text-xl font-bold text-[#0E1B2E]">
                        {employeeProgress.efficiency}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts Row - Compact */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Donut Chart */}
                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <h3 className="text-base font-semibold mb-3 text-[#0E1B2E]">
                    {employeeProgress.employeeName} Progress
                  </h3>
                  <div className="flex items-center gap-4">
                    <ResponsiveContainer width="60%" height={200}>
                      <PieChart>
                        <Pie
                          data={donutData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {donutData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-orange-500" />
                        <span className="text-sm text-[#0E1B2E]/70">
                          Pending: {100 - employeeProgress.overallProgress}%
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                        <span className="text-sm text-[#0E1B2E]/70">
                          Completed: {employeeProgress.overallProgress}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Time Spent vs Expected Chart */}
                <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-semibold text-[#0E1B2E]">
                      Time Spent vs. Expected
                    </h3>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-[#60a5fa]"></div>
                        <span className="text-[#0E1B2E]/70">Expected (h)</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-[#34d399]"></div>
                        <span className="text-[#0E1B2E]/70">Time spent (h)</span>
                      </div>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <ComposedChart data={employeeProgress.timeSpentData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="section"
                        stroke="#6b7280"
                        style={{ fontSize: '10px' }}
                      />
                      <YAxis
                        stroke="#6b7280"
                        style={{ fontSize: '10px' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="expected" fill="#60a5fa" name="Expected (h)" />
                      <Line type="monotone" dataKey="spent" stroke="#34d399" strokeWidth={2} name="Time spent (h)" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Section Progress Table - Compact */}
              <div className="p-4 rounded-lg border bg-white border-gray-200 shadow-sm">
                <h3 className="text-base font-semibold mb-3 text-[#0E1B2E]">
                  Section Progress
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          Section
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          Status
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          Expected (h)
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          Spent (h)
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          Progress
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[#0E1B2E]/70">
                          %
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {employeeProgress.sections.map((section, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-gray-200 hover:bg-[#0E1B2E]/5 transition-colors"
                        >
                          <td className="py-2 px-3 font-medium text-sm text-[#0E1B2E]">
                            {section.section}
                          </td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              section.status === 'Completed'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-orange-100 text-orange-700'
                            }`}>
                              {section.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-sm text-[#0E1B2E]/70">
                            {section.expectedHours} h
                          </td>
                          <td className="py-2 px-3 text-sm text-[#0E1B2E]/70">
                            {section.spentHours !== null ? `${section.spentHours} h` : '-'}
                          </td>
                          <td className="py-2 px-3">
                            <div className="w-24 h-1.5 rounded-full overflow-hidden bg-gray-200">
                              <div
                                className={`h-full ${
                                  section.completion > 100
                                    ? 'bg-red-500'
                                    : section.status === 'Completed'
                                    ? 'bg-green-400'
                                    : 'bg-blue-400'
                                }`}
                                style={{
                                  width: `${Math.min(section.completion, 100)}%`,
                                }}
                              />
                            </div>
                          </td>
                          <td className="py-2 px-3 text-sm text-[#0E1B2E]/70">
                            {section.spentHours !== null
                              ? `${section.completion}%`
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
            <Loader darkMode={false} message="Loading progress..." />
          )}
        </div>
      </div>
    </div>
  );
}

