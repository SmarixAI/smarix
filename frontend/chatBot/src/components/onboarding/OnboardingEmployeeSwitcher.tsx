export default function OnboardingEmployeeSwitcher({
  employees,
  selected,
  onSelect,
  darkMode = false
}: any) {
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
          Active Onboardings
        </h3>
        <p className={`text-xs mt-1 ${
          darkMode ? "text-gray-400" : "text-slate-500"
        }`}>
          Employees currently in onboarding process
        </p>
      </div>

      {/* EMPLOYEE LIST */}
      <div className="space-y-3">
        {employees.length === 0 ? (
          <div className="py-6 text-center">
            <p className={`text-sm ${
              darkMode ? "text-gray-400" : "text-slate-500"
            }`}>
              No active onboardings
            </p>
          </div>
        ) : (
          employees.map((emp: any) => {
            const isSelected = selected?.id === emp.id || selected?.employeeId === emp.employeeId || selected?.employee_id === emp.employee_id;

            return (
              <button
                key={emp.id || emp.employeeId || emp.employee_id}
                onClick={() => onSelect(emp)}
                className={`
                  w-full text-left rounded-2xl border-2 transition-all duration-300
                  transform hover:scale-105
                  ${isSelected
                    ? darkMode
                      ? 'border-indigo-500 bg-gradient-to-r from-indigo-900/50 to-purple-900/50 shadow-lg shadow-indigo-900/30'
                      : 'border-indigo-500 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-lg shadow-indigo-200'
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
                    <p className={`font-bold text-sm ${
                      darkMode ? "text-gray-100" : "text-slate-900"
                    }`}>
                      {emp.name}
                    </p>
                    <p className={`text-xs mt-1 ${
                      darkMode ? "text-gray-400" : "text-slate-600"
                    }`}>
                      {emp.role}
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
                    {emp.risk?.toUpperCase() || 'MEDIUM'}
                  </span>

                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

