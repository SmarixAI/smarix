"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Shield,
  User,
  Briefcase,
  Search,
  Filter,
  Database, // Added icon
} from "lucide-react";
import { Space_Grotesk, Fira_Code } from "next/font/google";
import Image from "next/image";
import { useAuth } from "@/components/auth/AuthContext";

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"] });
const firaCode = Fira_Code({ subsets: ["latin"] });

interface User {
  username: string;
  role: string;
  name?: string;
  employeeId?: string;
  designation?: string;
  status?: string;
  lastDay?: string;
  activeRepo?: string; // New Field
}

interface UserManagementViewProps {
  darkMode: boolean;
}

export default function UserManagementView({
  darkMode,
}: UserManagementViewProps) {
  const { token } = useAuth();

  const [users, setUsers] = useState<User[]>([]);
  const [availableRepos, setAvailableRepos] = useState<string[]>([]); // State for S3 repos
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRole, setFilterRole] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  // Form state for add/edit
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "",
    name: "",
    employeeId: "",
    designation: "",
    status: "general",
    lastDay: "",
    activeRepo: "", // New Field
  });

  // Use /auth prefix as per your previous request, but generic endpoints might be /api/admin
  // Adjust base URL if needed.
  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // --- Fetch Repositories from S3 ---
  const fetchRepositories = async () => {
    if (!token) return;
    try {
      // Assuming you added the endpoint to /auth or /admin
      const response = await fetch(`${baseURL}/auth/repositories`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableRepos(data.repositories || []);
      }
    } catch (error) {
      console.error("Error fetching repositories:", error);
    }
  };

  // --- Fetch Users ---
  const fetchUsers = async () => {
    if (!token) return;

    try {
      setLoading(true);
      const response = await fetch(`${baseURL}/auth/users`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();

        // 1. Normalize data structure
        const rawUsers = Array.isArray(data)
          ? data
          : data.users && Array.isArray(data.users)
            ? data.users
            : [];

        // 2. Map Data
        const mappedUsers: User[] = rawUsers.map((u: any) => ({
          username: u.username,
          role: u.role,
          name: u.name,
          designation: u.designation,
          status: u.status,
          employeeId: u.employee_id || u.employeeId || "",
          lastDay: u.last_day || u.lastDay || "",
          activeRepo: (u.active_repos && u.active_repos.length > 0) ? u.active_repos[0] : "",
        }));

        setUsers(mappedUsers);
      } else {
        setError("Failed to fetch users");
      }
    } catch (error) {
      console.error("Error fetching users:", error);
      setError("Error loading users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
      fetchRepositories();
    }
  }, [token]);

  // Clear messages after 3 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // --- Add User ---
  const handleAddUser = async () => {
    try {
      setModalError(null);

      if (!formData.username || !formData.password || !formData.role) {
        setModalError("Username, password, and role are required");
        return;
      }

      if (formData.employeeId) {
        const existingUser = users.find(
          (u) =>
            u.employeeId &&
            u.employeeId.toLowerCase() === formData.employeeId.toLowerCase(),
        );
        if (existingUser) {
          setModalError(
            `Employee ID "${formData.employeeId}" is already assigned to user "${existingUser.username}"`,
          );
          return;
        }
      }

      const response = await fetch(`${baseURL}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
          role: formData.role,
          name: formData.name || undefined,
          employee_id: formData.employeeId || undefined,
          designation: formData.designation || undefined,
          status: formData.status || "general",
          active_repos: formData.activeRepo ? [formData.activeRepo] : [],
          last_day: undefined,
          managers: [],
        }),
      });

      if (response.ok) {
        setSuccess("User created successfully");
        setShowAddModal(false);
        setModalError(null);
        resetForm();
        fetchUsers();
      } else {
        const data = await response.json();
        setModalError(data.detail || "Failed to create user");
      }
    } catch (error) {
      console.error("Error creating user:", error);
      setModalError("Error creating user");
    }
  };

  // --- Update User ---
  const handleUpdateUser = async (username: string) => {
    try {
      const response = await fetch(
        `${baseURL}/auth/users/${encodeURIComponent(username)}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            role: formData.role,
            name: formData.name,
            employee_id: formData.employeeId,
            designation: formData.designation,
            status: formData.status,
            active_repos: formData.activeRepo ? [formData.activeRepo] : [],
            last_day: formData.status === "offboard" ? formData.lastDay : null,
          }),
        },
      );

      if (response.ok) {
        setSuccess("User updated successfully");
        setEditingUser(null);
        resetForm();
        fetchUsers();
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to update user");
      }
    } catch (error) {
      console.error("Error updating user:", error);
      setError("Error updating user");
    }
  };

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `${baseURL}/auth/users/${encodeURIComponent(username)}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.ok) {
        setSuccess("User deleted successfully");
        fetchUsers();
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to delete user");
      }
    } catch (error) {
      console.error("Error deleting user:", error);
      setError("Error deleting user");
    }
  };

  const resetForm = () => {
    setFormData({
      username: "",
      password: "",
      role: "",
      name: "",
      employeeId: "",
      designation: "",
      status: "general",
      activeRepo: "",
      lastDay: "",
    });
  };

  const handleOpenAddModal = () => {
    resetForm();
    setModalError(null);
    setShowAddModal(true);
  };

  const startEdit = (user: User) => {
    setEditingUser(user.username);
    setFormData({
      username: user.username,
      password: "",
      role: user.role,
      name: user.name || "",
      employeeId: user.employeeId || "",
      designation: user.designation || "",
      status: user.status || "general",
      activeRepo: user.activeRepo || "",
      lastDay: user.lastDay || "",
    });
  };

  const cancelEdit = () => {
    setEditingUser(null);
    resetForm();
  };

  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case "admin":
        return <Shield className="w-4 h-4" />;
      case "manager":
        return <Briefcase className="w-4 h-4" />;
      default:
        return <User className="w-4 h-4" />;
    }
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      searchQuery === "" ||
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.name &&
        user.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (user.employeeId &&
        user.employeeId.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesRole =
      filterRole === "all" ||
      user.role.toLowerCase() === filterRole.toLowerCase();
    const matchesStatus =
      filterStatus === "all" || (user.status || "general") === filterStatus;

    return matchesSearch && matchesRole && matchesStatus;
  });

  if (loading) {
    return (
      <div className="relative rounded-xl shadow-lg p-6 bg-white/80 backdrop-blur-xl border border-gray-200/50">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0E1B2E] mx-auto mb-4"></div>
            <p className={`${firaCode.className} text-[#0E1B2E]/60`}>
              Loading users...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative rounded-xl shadow-lg p-6 bg-white/80 backdrop-blur-xl border border-gray-200/50">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#0E1B2E] rounded-xl flex items-center justify-center overflow-hidden">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={24}
                  height={24}
                  className="w-6 h-6 object-contain"
                />
              </div>
              <div>
                <h2
                  className={`${spaceGrotesk.className} text-2xl font-bold text-[#0E1B2E]`}
                >
                  User Management
                </h2>
                <p
                  className={`${firaCode.className} text-sm text-[#0E1B2E]/60`}
                >
                  Manage users and repository assignments
                </p>
              </div>
            </div>
            <button
              onClick={handleOpenAddModal}
              className={`${spaceGrotesk.className} flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all bg-[#0E1B2E] hover:bg-[#0E1B2E]/90 text-white shadow-lg shadow-[#0E1B2E]/20 hover:shadow-xl hover:shadow-[#0E1B2E]/30`}
            >
              <Plus className="w-5 h-5" />
              Add User
            </button>
          </div>

          {/* Messages */}
          {error && (
            <div
              className={`mb-4 p-3 rounded-lg bg-rose-100/80 border border-rose-200/50 text-rose-700 text-sm ${firaCode.className}`}
            >
              {error}
            </div>
          )}
          {success && (
            <div
              className={`mb-4 p-3 rounded-lg bg-emerald-100/80 border border-emerald-200/50 text-emerald-700 text-sm ${firaCode.className}`}
            >
              {success}
            </div>
          )}

          {/* Search and Filter Bar */}
          <div className="mt-4 flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by username, name, or employee ID..."
                className={`${firaCode.className} w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200/50 outline-none transition-colors bg-white/80 backdrop-blur-sm text-[#0E1B2E] focus:border-[#0E1B2E] placeholder-[#0E1B2E]/40`}
              />
            </div>

            <div className="relative">
              <Filter
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5"
                color="black"
                strokeWidth={2}
              />
              <select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className={`${firaCode.className} pl-10 pr-8 py-2 rounded-xl border border-gray-200/50 outline-none transition-colors appearance-none bg-white/80 backdrop-blur-sm text-[#0E1B2E] focus:border-[#0E1B2E]`}
              >
                <option value="all">All Roles</option>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="employee">Employee</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="relative rounded-xl shadow-lg p-6 bg-white/80 backdrop-blur-xl border border-gray-200/50">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />

        <div className="relative z-10 overflow-x-auto min-h-[400px]">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200/50">
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  User
                </th>
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  Role
                </th>
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  Details
                </th>
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  Active Repo
                </th>
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  Status
                </th>
                <th
                  className={`${spaceGrotesk.className} text-left py-3 px-4 text-sm font-semibold text-[#0E1B2E]`}
                >
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className={`text-center py-8 ${firaCode.className} text-[#0E1B2E]/60`}
                  >
                    {users.length === 0
                      ? "No users found"
                      : "No users match your search/filters"}
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr
                    key={user.username}
                    className="border-b border-gray-200/50 transition-colors hover:bg-[#0E1B2E]/5"
                  >
                    {editingUser === user.username ? (
                      <>
                        <td className="py-3 px-4">
                          <div className="flex flex-col gap-1">
                            <input
                              type="text"
                              disabled
                              value={formData.username}
                              className={`${firaCode.className} w-full px-2 py-1 rounded bg-gray-100 text-gray-500 text-xs`}
                            />
                            <input
                              type="text"
                              value={formData.name}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  name: e.target.value,
                                })
                              }
                              placeholder="Full Name"
                              className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                            />
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={formData.role}
                            onChange={(e) =>
                              setFormData({ ...formData, role: e.target.value })
                            }
                            className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                          >
                            <option value="admin">Admin</option>
                            <option value="manager">Manager</option>
                            <option value="employee">Employee</option>
                          </select>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col gap-1">
                            <input
                              type="text"
                              value={formData.employeeId}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  employeeId: e.target.value,
                                })
                              }
                              placeholder="ID"
                              className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                            />
                            <input
                              type="text"
                              value={formData.designation}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  designation: e.target.value,
                                })
                              }
                              placeholder="Designation"
                              className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                            />
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={formData.activeRepo}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                activeRepo: e.target.value,
                              })
                            }
                            className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                          >
                            <option value="">Select Repo</option>
                            {availableRepos.map((repo) => (
                              <option key={repo} value={repo}>
                                {repo}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={formData.status}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                status: e.target.value,
                              })
                            }
                            className={`${firaCode.className} w-full px-2 py-1 rounded text-sm border border-gray-200 outline-none focus:border-[#0E1B2E]`}
                          >
                            <option value="general">General</option>
                            <option value="onboard">Onboard</option>
                            <option value="offboard">Offboard</option>
                          </select>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleUpdateUser(user.username)}
                              className="p-1.5 rounded-lg hover:bg-emerald-100 text-emerald-600"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-3 px-4">
                          <div
                            className={`${spaceGrotesk.className} font-medium text-[#0E1B2E]`}
                          >
                            {user.username}
                          </div>
                          <div
                            className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}
                          >
                            {user.name}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2 text-[#0E1B2E]">
                            {getRoleIcon(user.role)}
                            <span
                              className={`${spaceGrotesk.className} font-medium capitalize text-sm`}
                            >
                              {user.role}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div
                            className={`${firaCode.className} text-xs text-[#0E1B2E]/70`}
                          >
                            ID: {user.employeeId || "-"}
                          </div>
                          <div
                            className={`${firaCode.className} text-xs text-[#0E1B2E]/70`}
                          >
                            {user.designation || "-"}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {user.activeRepo ? (
                            <span
                              className={`${firaCode.className} flex items-center gap-1.5 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-100`}
                            >
                              <Database className="w-3 h-3" />
                              {user.activeRepo}
                            </span>
                          ) : (
                            <span
                              className={`${firaCode.className} text-xs text-gray-400 italic`}
                            >
                              Unassigned
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`${firaCode.className} px-2 py-1 rounded-full text-xs font-medium ${
                              user.status === "onboard"
                                ? "bg-emerald-100 text-emerald-700"
                                : user.status === "offboard"
                                  ? "bg-rose-100 text-rose-700"
                                  : "bg-gray-100 text-[#0E1B2E]/70"
                            }`}
                          >
                            {user.status || "general"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => startEdit(user)}
                              className="p-1.5 rounded-lg hover:bg-[#0E1B2E]/10 text-[#0E1B2E]/70"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.username)}
                              className="p-1.5 rounded-lg hover:bg-rose-100 text-rose-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="relative w-full max-w-md max-h-[90vh] flex flex-col rounded-xl shadow-2xl bg-white/95 backdrop-blur-xl border border-gray-200/50">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none rounded-xl" />

            <div className="relative z-10 flex items-center justify-between p-6 pb-4 border-b border-gray-200/50">
              <h3
                className={`${spaceGrotesk.className} text-xl font-bold text-[#0E1B2E]`}
              >
                Add New User
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setModalError(null);
                  resetForm();
                }}
                className="p-1 rounded-lg transition-colors hover:bg-[#0E1B2E]/10 text-[#0E1B2E]/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="relative z-10 flex-1 overflow-y-auto p-6">
              {modalError && (
                <div
                  className={`mb-4 p-3 rounded-lg bg-rose-100/80 border border-rose-200/50 text-rose-700 text-sm ${firaCode.className}`}
                >
                  {modalError}
                </div>
              )}

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Username *
                    </label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) =>
                        setFormData({ ...formData, username: e.target.value })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Password *
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                      placeholder="password"
                    />
                  </div>
                </div>

                <div>
                  <label
                    className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                  >
                    Role *
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value })
                    }
                    className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                  >
                    <option value="">Select role</option>
                    <option value="admin">Admin</option>
                    <option value="manager">Manager</option>
                    <option value="employee">Employee</option>
                  </select>
                </div>

                <div>
                  <label
                    className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                  >
                    Active Repository
                  </label>
                  <select
                    value={formData.activeRepo}
                    onChange={(e) =>
                      setFormData({ ...formData, activeRepo: e.target.value })
                    }
                    className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                  >
                    <option value="">Select a Repository</option>
                    {availableRepos.map((repo) => (
                      <option key={repo} value={repo}>
                        {repo}
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-gray-400 mt-1 ml-1">
                    Assign a specific GitHub repository to this user
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                    />
                  </div>
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Employee ID
                    </label>
                    <input
                      type="text"
                      value={formData.employeeId}
                      onChange={(e) =>
                        setFormData({ ...formData, employeeId: e.target.value })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Designation
                    </label>
                    <input
                      type="text"
                      value={formData.designation}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          designation: e.target.value,
                        })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                    />
                  </div>
                  <div>
                    <label
                      className={`${spaceGrotesk.className} block text-sm font-medium mb-1 text-[#0E1B2E]`}
                    >
                      Status
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) =>
                        setFormData({ ...formData, status: e.target.value })
                      }
                      className={`${firaCode.className} w-full px-3 py-2 rounded-xl border border-gray-200/50 outline-none focus:border-[#0E1B2E]`}
                    >
                      <option value="general">General</option>
                      <option value="onboard">Onboard</option>
                      <option value="offboard">Offboard</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative z-10 p-6 pt-4 border-t border-gray-200/50">
              <div className="flex gap-3">
                <button
                  onClick={handleAddUser}
                  className={`${spaceGrotesk.className} flex-1 px-4 py-2.5 rounded-xl transition-all bg-[#0E1B2E] hover:bg-[#0E1B2E]/90 text-white shadow-lg shadow-[#0E1B2E]/20 hover:shadow-xl hover:shadow-[#0E1B2E]/30`}
                >
                  Create User
                </button>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setModalError(null);
                    resetForm();
                  }}
                  className={`${spaceGrotesk.className} px-4 py-2.5 rounded-xl transition-colors bg-gray-100 hover:bg-gray-200 text-[#0E1B2E]`}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
