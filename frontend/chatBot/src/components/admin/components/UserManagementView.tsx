"use client";

import { useState, useEffect } from "react";
import { Users, Plus, Edit2, Trash2, Save, X, Shield, User, Briefcase, Search, Filter } from "lucide-react";

interface User {
  username: string;
  role: string;
  name?: string;
  employeeId?: string;
  designation?: string;
  status?: string;
  lastDay?: string;
}

interface UserManagementViewProps {
  darkMode: boolean;
}

export default function UserManagementView({ darkMode }: UserManagementViewProps) {
  const [users, setUsers] = useState<User[]>([]);
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
  });

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch users
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${baseURL}/admin/users`);
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
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
    fetchUsers();
  }, []);

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

  const handleAddUser = async () => {
    try {
      // Clear previous modal errors
      setModalError(null);
      
      if (!formData.username || !formData.password || !formData.role) {
        setModalError("Username, password, and role are required");
        return;
      }

      // Validate employeeId uniqueness
      if (formData.employeeId) {
        const existingUser = users.find(
          (u) => u.employeeId && u.employeeId.toLowerCase() === formData.employeeId.toLowerCase()
        );
        if (existingUser) {
          setModalError(`Employee ID "${formData.employeeId}" is already assigned to user "${existingUser.username}"`);
          return;
        }
      }

      const response = await fetch(`${baseURL}/admin/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
          role: formData.role,
          name: formData.name || undefined,
          employeeId: formData.employeeId || undefined,
          designation: formData.designation || undefined,
          status: formData.status || "general",
          lastDay: undefined, // Don't send lastDay for new users
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

  const handleUpdateUser = async (username: string) => {
    try {
      // Validate employeeId uniqueness (exclude current user)
      if (formData.employeeId) {
        const existingUser = users.find(
          (u) =>
            u.username !== username &&
            u.employeeId &&
            u.employeeId.toLowerCase() === formData.employeeId.toLowerCase()
        );
        if (existingUser) {
          setError(`Employee ID "${formData.employeeId}" is already assigned to user "${existingUser.username}"`);
          return;
        }
      }

      const response = await fetch(`${baseURL}/admin/users/${encodeURIComponent(username)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.username !== username ? formData.username : undefined,
          password: formData.password || undefined,
          role: formData.role,
          name: formData.name || undefined,
          employeeId: formData.employeeId || undefined,
          designation: formData.designation || undefined,
          status: formData.status,
          lastDay: formData.status === "offboard" ? formData.lastDay || undefined : undefined,
        }),
      });

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
      const response = await fetch(`${baseURL}/admin/users/${encodeURIComponent(username)}`, {
        method: "DELETE",
      });

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
      lastDay: "",
    });
  };

  // Reset form when opening add modal
  const handleOpenAddModal = () => {
    setFormData({
      username: "",
      password: "",
      role: "",
      name: "",
      employeeId: "",
      designation: "",
      status: "general",
      lastDay: "",
    });
    setModalError(null);
    setShowAddModal(true);
  };

  const startEdit = (user: User) => {
    setEditingUser(user.username);
    setFormData({
      username: user.username,
      password: "", // Don't pre-fill password
      role: user.role,
      name: user.name || "",
      employeeId: user.employeeId || "",
      designation: user.designation || "",
      status: user.status || "general",
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

  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case "admin":
        return darkMode ? "text-red-400" : "text-red-600";
      case "manager":
        return darkMode ? "text-blue-400" : "text-blue-600";
      default:
        return darkMode ? "text-gray-400" : "text-gray-600";
    }
  };

  // Filter users based on search and filters
  const filteredUsers = users.filter((user) => {
    // Search filter
    const matchesSearch =
      searchQuery === "" ||
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.name && user.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (user.employeeId && user.employeeId.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (user.designation && user.designation.toLowerCase().includes(searchQuery.toLowerCase()));

    // Role filter
    const matchesRole = filterRole === "all" || user.role.toLowerCase() === filterRole.toLowerCase();

    // Status filter
    const matchesStatus = filterStatus === "all" || (user.status || "general") === filterStatus;

    return matchesSearch && matchesRole && matchesStatus;
  });

  if (loading) {
    return (
      <div className={`p-6 rounded-2xl ${darkMode ? "glass-card-dark" : "glass-card-light"}`}>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className={darkMode ? "text-gray-400" : "text-slate-600"}>Loading users...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`p-6 rounded-2xl ${darkMode ? "glass-card-dark" : "glass-card-light"}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={`p-3 rounded-xl ${
                darkMode
                  ? "bg-gradient-to-br from-purple-600 to-pink-600"
                  : "bg-gradient-to-br from-purple-500 to-pink-500"
              }`}
            >
              <Users className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                User Management
              </h2>
              <p className={`text-sm ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                Manage users, roles, and permissions
              </p>
            </div>
          </div>
          <button
            onClick={handleOpenAddModal}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              darkMode
                ? "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white"
                : "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
            }`}
          >
            <Plus className="w-5 h-5" />
            Add User
          </button>
        </div>

        {/* Messages */}
        {error && (
          <div
            className={`mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm`}
          >
            {error}
          </div>
        )}
        {success && (
          <div
            className={`mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm`}
          >
            {success}
          </div>
        )}

        {/* Search and Filter Bar */}
        <div className="mt-4 flex flex-col sm:flex-row gap-3">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <Search
              className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by username, name, employee ID, or designation..."
              className={`w-full pl-10 pr-4 py-2 rounded-lg border outline-none transition-colors ${
                darkMode
                  ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500 placeholder-gray-500"
                  : "bg-white text-slate-900 border-slate-300 focus:border-blue-500 placeholder-slate-400"
              }`}
            />
          </div>

          {/* Role Filter */}
          <div className="relative">
            <Filter
              className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${
                darkMode ? "text-gray-400" : "text-slate-500"
              }`}
            />
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className={`pl-10 pr-8 py-2 rounded-lg border outline-none transition-colors appearance-none ${
                darkMode
                  ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                  : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
              }`}
            >
              <option value="all">All Roles</option>
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="employee">Employee</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="relative">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className={`px-4 py-2 rounded-lg border outline-none transition-colors appearance-none ${
                darkMode
                  ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                  : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
              }`}
            >
              <option value="all">All Status</option>
              <option value="general">General</option>
              <option value="onboard">Onboard</option>
              <option value="offboard">Offboard</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className={`p-6 rounded-2xl ${darkMode ? "glass-card-dark" : "glass-card-light"}`}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className={`border-b ${darkMode ? "border-gray-700" : "border-slate-200"}`}>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Username
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Name
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Role
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Employee ID
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Designation
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Status
                </th>
                <th className={`text-left py-3 px-4 text-sm font-semibold ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className={`text-center py-8 ${darkMode ? "text-gray-400" : "text-slate-500"}`}>
                    {users.length === 0 ? "No users found" : "No users match your search/filters"}
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr
                    key={user.username}
                    className={`border-b transition-colors ${
                      darkMode
                        ? "border-gray-700 hover:bg-gray-800/50"
                        : "border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {editingUser === user.username ? (
                      <>
                        <td className="py-3 px-4">
                          <input
                            type="text"
                            value={formData.username}
                            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                            placeholder="Username"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                          />
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={formData.role}
                            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                          >
                            <option value="admin">Admin</option>
                            <option value="manager">Manager</option>
                            <option value="employee">Employee</option>
                          </select>
                        </td>
                        <td className="py-3 px-4">
                          <input
                            type="text"
                            value={formData.employeeId}
                            onChange={(e) => setFormData({ ...formData, employeeId: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                          />
                        </td>
                        <td className="py-3 px-4">
                          <input
                            type="text"
                            value={formData.designation}
                            onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                          />
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={formData.status}
                            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                            className={`w-full px-2 py-1 rounded text-sm mb-2 ${
                              darkMode
                                ? "bg-gray-700 text-white border-gray-600"
                                : "bg-white text-slate-900 border-slate-300"
                            } border outline-none`}
                          >
                            <option value="general">General</option>
                            <option value="onboard">Onboard</option>
                            <option value="offboard">Offboard</option>
                          </select>
                          {formData.status === "offboard" && (
                            <div className="mt-2">
                              <label className={`block text-xs font-medium mb-1 ${darkMode ? "text-gray-400" : "text-slate-600"}`}>
                                Last Day
                              </label>
                              <input
                                type="date"
                                value={formData.lastDay}
                                onChange={(e) => setFormData({ ...formData, lastDay: e.target.value })}
                                className={`w-full px-2 py-1 rounded text-sm ${
                                  darkMode
                                    ? "bg-gray-700 text-white border-gray-600"
                                    : "bg-white text-slate-900 border-slate-300"
                                } border outline-none`}
                              />
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleUpdateUser(user.username)}
                              className={`p-1.5 rounded transition-colors ${
                                darkMode
                                  ? "hover:bg-green-600/20 text-green-400"
                                  : "hover:bg-green-100 text-green-600"
                              }`}
                              title="Save"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={cancelEdit}
                              className={`p-1.5 rounded transition-colors ${
                                darkMode
                                  ? "hover:bg-gray-700 text-gray-400"
                                  : "hover:bg-slate-200 text-slate-600"
                              }`}
                              title="Cancel"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className={`py-3 px-4 font-medium ${darkMode ? "text-white" : "text-slate-900"}`}>
                          {user.username}
                        </td>
                        <td className={`py-3 px-4 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                          {user.name || "-"}
                        </td>
                        <td className="py-3 px-4">
                          <div className={`flex items-center gap-2 ${getRoleColor(user.role)}`}>
                            {getRoleIcon(user.role)}
                            <span className="font-medium capitalize">{user.role}</span>
                          </div>
                        </td>
                        <td className={`py-3 px-4 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                          {user.employeeId || "-"}
                        </td>
                        <td className={`py-3 px-4 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                          {user.designation || "-"}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              user.status === "onboard"
                                ? darkMode
                                  ? "bg-green-500/20 text-green-400"
                                  : "bg-green-100 text-green-700"
                                : user.status === "offboard"
                                ? darkMode
                                  ? "bg-red-500/20 text-red-400"
                                  : "bg-red-100 text-red-700"
                                : darkMode
                                ? "bg-gray-700 text-gray-300"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {user.status || "general"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => startEdit(user)}
                              className={`p-1.5 rounded transition-colors ${
                                darkMode
                                  ? "hover:bg-blue-600/20 text-blue-400"
                                  : "hover:bg-blue-100 text-blue-600"
                              }`}
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.username)}
                              className={`p-1.5 rounded transition-colors ${
                                darkMode
                                  ? "hover:bg-red-600/20 text-red-400"
                                  : "hover:bg-red-100 text-red-600"
                              }`}
                              title="Delete"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div
            className={`w-full max-w-md max-h-[90vh] flex flex-col rounded-2xl shadow-2xl ${
              darkMode ? "glass-card-dark" : "glass-card-light"
            }`}
          >
            <div className="flex items-center justify-between p-6 pb-4 border-b border-gray-700/50 dark:border-slate-200/20">
              <h3 className={`text-xl font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                Add New User
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setModalError(null);
                  resetForm();
                }}
                className={`p-1 rounded transition-colors ${
                  darkMode ? "hover:bg-gray-700 text-gray-400" : "hover:bg-slate-200 text-slate-600"
                }`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Modal Error Message */}
              {modalError && (
                <div
                  className={`mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm`}
                >
                  {modalError}
                </div>
              )}
              
              <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Username *
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  autoComplete="off"
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  placeholder="Enter username"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Password *
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  autoComplete="new-password"
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  placeholder="Enter password"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Role *
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  required
                >
                  <option value="">Select role</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="employee">Employee</option>
                </select>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  placeholder="Enter full name"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Employee ID
                </label>
                <input
                  type="text"
                  value={formData.employeeId}
                  onChange={(e) => setFormData({ ...formData, employeeId: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  placeholder="Enter employee ID"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Designation
                </label>
                <input
                  type="text"
                  value={formData.designation}
                  onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                  placeholder="Enter designation"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${darkMode ? "text-gray-300" : "text-slate-700"}`}>
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border outline-none transition-colors ${
                    darkMode
                      ? "bg-gray-700 text-white border-gray-600 focus:border-blue-500"
                      : "bg-white text-slate-900 border-slate-300 focus:border-blue-500"
                  }`}
                >
                  <option value="general">General</option>
                  <option value="onboard">Onboard</option>
                  <option value="offboard">Offboard</option>
                </select>
              </div>

              </div>
            </div>

            <div className="p-6 pt-4 border-t border-gray-700/50 dark:border-slate-200/20">
              <div className="flex gap-3">
                <button
                  onClick={handleAddUser}
                  className={`flex-1 px-4 py-2 rounded-lg transition-all ${
                    darkMode
                      ? "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white"
                      : "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                  }`}
                >
                  Create User
                </button>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setModalError(null);
                    resetForm();
                  }}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    darkMode
                      ? "bg-gray-700 hover:bg-gray-600 text-gray-300"
                      : "bg-slate-200 hover:bg-slate-300 text-slate-700"
                  }`}
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

