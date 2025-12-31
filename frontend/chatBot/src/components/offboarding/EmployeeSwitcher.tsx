export default function EmployeeSwitcher({
  employees,
  selected,
  onSelect,
  darkMode = false
}: any) {
  // Helper function to get a unique identifier for an employee
  const getEmployeeIdentifier = (emp: any): string | null => {
    if (!emp) return null;
    // Priority: employeeId > employee_id > id > name
    return emp.employeeId || emp.employee_id || emp.id || emp.name || null;
  };

  // Get the selected employee's identifier
  const selectedIdentifier = getEmployeeIdentifier(selected);

  return (
    <div className={`backdrop-blur-lg rounded-3xl shadow-xl border p-6 space-y-4 transform transition-all duration-300 hover:shadow-2xl ${
      darkMode
        ? "bg-gray-800/80 border-gray-700"
        : "bg-white/80 border-slate-200/50"
    }`}>

      {/* HEADER */}
      <div className={`border-b pb-4 ${
        darkMode ? "border-gray-700" : "border-slate-200"
      }`}>
        <h3 className={`text-lg font-bold ${
          darkMode
            ? "bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent"
            : "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent"
        }`}>
          Active Offboardings
        </h3>
        <p className={`text-xs mt-1 ${
          darkMode ? "text-gray-400" : "text-slate-500"
        }`}>
          Employees currently in exit process
        </p>
      </div>

      {/* EMPLOYEE LIST */}
      <div className="space-y-3">
        {employees.map((emp: any) => {
          // Get this employee's identifier
          const empIdentifier = getEmployeeIdentifier(emp);
          
          // Only selected if identifiers match exactly and are not null
          const isSelected = selectedIdentifier !== null && 
                            empIdentifier !== null && 
                            selectedIdentifier === empIdentifier;

          return (
            <button
              key={emp.id || emp.employeeId || emp.employee_id}
              onClick={() => onSelect(emp)}
              className={`
                w-full text-left rounded-2xl border-2 transition-all duration-300
                transform hover:scale-105
                ${isSelected
                  ? darkMode
                    ? 'border-indigo-400 bg-gradient-to-r from-indigo-900/70 to-purple-900/70 shadow-xl shadow-indigo-500/50 ring-2 ring-indigo-500/50'
                    : 'border-indigo-500 bg-gradient-to-r from-indigo-100 to-purple-100 shadow-xl shadow-indigo-300/50 ring-2 ring-indigo-300/50'
                  : darkMode
                    ? 'border-gray-700 bg-gray-800 hover:bg-gray-700 hover:border-gray-600 hover:shadow-md'
                    : 'border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 hover:shadow-md'
                }
              `}
            >
              <div className="flex items-center gap-4 p-4">

                {/* LEFT ACCENT */}
                <div
                  className={`w-2 rounded-full h-12 shadow-md ${
                    emp.risk === 'high'
                      ? darkMode
                        ? 'bg-gradient-to-b from-red-600 to-red-700'
                        : 'bg-gradient-to-b from-red-500 to-red-600'
                      : emp.risk === 'medium'
                      ? darkMode
                        ? 'bg-gradient-to-b from-yellow-500 to-yellow-600'
                        : 'bg-gradient-to-b from-yellow-400 to-yellow-500'
                      : darkMode
                        ? 'bg-gradient-to-b from-green-500 to-green-600'
                        : 'bg-gradient-to-b from-green-500 to-green-600'
                  }`}
                />

                {/* MAIN CONTENT */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className={`font-bold text-sm ${
                      isSelected
                        ? darkMode ? "text-indigo-200" : "text-indigo-700"
                        : darkMode ? "text-gray-100" : "text-slate-900"
                    }`}>
                      {emp.name}
                    </p>
                    {isSelected && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        darkMode 
                          ? 'bg-indigo-500/30 text-indigo-200 border border-indigo-400/50'
                          : 'bg-indigo-500/20 text-indigo-700 border border-indigo-400/50'
                      }`}>
                        Selected
                      </span>
                    )}
                  </div>
                  <p className={`text-xs mt-1 ${
                    isSelected
                      ? darkMode ? "text-indigo-300" : "text-indigo-600"
                      : darkMode ? "text-gray-400" : "text-slate-600"
                  }`}>
                    {emp.designation || emp.role}
                  </p>
                </div>

                {/* RISK BADGE */}
                <span
                  className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap shadow-md border-2 ${
                    emp.risk === 'high'
                      ? darkMode
                        ? 'bg-gradient-to-r from-red-900/50 to-red-900/70 text-red-300 border-red-700'
                        : 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border-red-300'
                      : emp.risk === 'medium'
                      ? darkMode
                        ? 'bg-gradient-to-r from-yellow-900/50 to-yellow-900/70 text-yellow-300 border-yellow-700'
                        : 'bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border-yellow-300'
                      : darkMode
                        ? 'bg-gradient-to-r from-green-900/50 to-green-900/70 text-green-300 border-green-700'
                        : 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border-green-300'
                  }`}
                >
                  {emp.risk.toUpperCase()}
                </span>

              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
