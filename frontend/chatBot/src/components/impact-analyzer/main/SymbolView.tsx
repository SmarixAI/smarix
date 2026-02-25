"use client";

import { useMemo, useState } from "react";

interface Props {
  fileSymbols: any;
}

type SortOption = "blast" | "fanin" | "severity";

export default function SymbolView({ fileSymbols }: Props) {
  const [selectedSymbol, setSelectedSymbol] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState<SortOption>("blast");

  if (!fileSymbols || !fileSymbols.symbols) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#0B1220] text-gray-500">
        Select a file to inspect symbols
      </div>
    );
  }

  // ================= Dynamic Type Options =================
  const uniqueTypes = useMemo(() => {
    return [
      "ALL",
      ...Array.from(new Set(fileSymbols.symbols.map((s: any) => s.type))),
    ];
  }, [fileSymbols]);

  // ================= Filter + Sort =================
  const processedSymbols = useMemo(() => {
    let symbols = [...fileSymbols.symbols];

    if (search) {
      symbols = symbols.filter((s: any) =>
        s.name?.toLowerCase().includes(search.toLowerCase())
      );
    }

    if (severityFilter !== "ALL") {
      symbols = symbols.filter((s: any) => s.severity === severityFilter);
    }

    if (typeFilter !== "ALL") {
      symbols = symbols.filter((s: any) => s.type === typeFilter);
    }

    symbols.sort((a: any, b: any) => {
      if (sortBy === "blast") return (b.blast_radius || 0) - (a.blast_radius || 0);
      if (sortBy === "fanin") return (b.fan_in || 0) - (a.fan_in || 0);
      if (sortBy === "severity") {
        const order: any = { HIGH: 3, MEDIUM: 2, LOW: 1 };
        return (order[b.severity] || 0) - (order[a.severity] || 0);
      }
      return 0;
    });

    return symbols;
  }, [fileSymbols, search, severityFilter, typeFilter, sortBy]);

  const highRiskCount = fileSymbols.symbols.filter(
    (s: any) => s.severity === "HIGH"
  ).length;

  // ================= LIST VIEW =================
  if (!selectedSymbol) {
    return (
      <div className="flex-1 min-h-0 flex flex-col bg-[#0B1220] text-sm">

        {/* HEADER */}
        <div className="sticky top-0 z-10 bg-[#0F172A] border-b border-[#1F2937] p-5 space-y-4">
          <div>
            <div className="text-xl font-semibold text-white">
              File Symbols
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {fileSymbols.total_symbols} total •{" "}
              <span className="text-red-400 font-medium">
                {highRiskCount} high risk
              </span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex gap-3 flex-wrap">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbols..."
              className="bg-[#111827] border border-[#1F2937] rounded-lg px-3 py-2 text-xs text-gray-300 w-64 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-[#111827] border border-[#1F2937] rounded-lg px-3 py-2 text-xs text-gray-300"
            >
              <option value="ALL">All Severities</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-[#111827] border border-[#1F2937] rounded-lg px-3 py-2 text-xs text-gray-300"
            >
              {uniqueTypes.map((type) => (
                <option key={type} value={type}>
                  {type === "ALL" ? "All Types" : type}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="bg-[#111827] border border-[#1F2937] rounded-lg px-3 py-2 text-xs text-gray-300"
            >
              <option value="blast">Sort by Blast Radius</option>
              <option value="fanin">Sort by Fan-in</option>
              <option value="severity">Sort by Severity</option>
            </select>
          </div>
        </div>

        {/* SYMBOL LIST */}
        <div className="flex-1 min-h-0 overflow-y-auto p-6 space-y-4">
          {processedSymbols.length === 0 && (
            <div className="text-gray-500 text-xs">
              No symbols match current filters.
            </div>
          )}

          {processedSymbols.map((s: any) => (
            <div
              key={s.symbol}
              onClick={() => setSelectedSymbol(s)}
              className="group p-4 bg-[#111827] border border-[#1F2937]
                         rounded-xl cursor-pointer
                         hover:border-blue-500/40
                         hover:bg-[#162036]
                         transition-all duration-200"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-white font-medium group-hover:text-blue-400 transition">
                    {s.name}
                  </div>
                  <div className="text-xs text-gray-400 mt-1 uppercase tracking-wide">
                    {s.type}
                  </div>
                </div>
                <SeverityBadge severity={s.severity} />
              </div>

              <div className="flex gap-6 mt-4 text-xs text-gray-400">
                <MetricSmall label="Fan-in" value={s.fan_in} />
                <MetricSmall label="Fan-out" value={s.fan_out} />
                <MetricSmall label="Blast" value={s.blast_radius} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ================= DETAIL VIEW =================
  return (
    <div className="flex-1 min-h-0 overflow-y-auto bg-[#0B1220] p-8">

      <button
        onClick={() => setSelectedSymbol(null)}
        className="text-xs text-blue-400 mb-6 hover:opacity-80"
      >
        ← Back to symbols
      </button>

      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="text-2xl font-semibold text-white">
            {selectedSymbol.name}
          </div>
          <div className="text-xs uppercase tracking-wide text-gray-400 mt-1">
            {selectedSymbol.type}
          </div>
        </div>
        <SeverityBadge severity={selectedSymbol.severity} />
      </div>

      <Card title="Signature">
        <div className="text-gray-300 text-sm">
          <div className="mb-2">
            <span className="text-gray-500">Parameters:</span>{" "}
            {(selectedSymbol.parameters || []).length === 0
              ? "None"
              : selectedSymbol.parameters
                  .map((p: any) =>
                    p.type ? `${p.name}: ${p.type}` : p.name
                  )
                  .join(", ")}
          </div>
          <div>
            <span className="text-gray-500">Return Type:</span>{" "}
            {selectedSymbol.return_type || "None"}
          </div>
        </div>
      </Card>

      <Card title="Risk Metrics">
        <div className="grid grid-cols-3 gap-6 text-center">
          <MetricLarge label="Fan-in" value={selectedSymbol.fan_in} />
          <MetricLarge label="Fan-out" value={selectedSymbol.fan_out} />
          <MetricLarge label="Blast Radius" value={selectedSymbol.blast_radius} />
        </div>
      </Card>

      {selectedSymbol.docstring && (
        <Card title="Documentation">
          <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
            {selectedSymbol.docstring}
          </div>
        </Card>
      )}
    </div>
  );
}

/* ================= COMPONENTS ================= */

function Card({ title, children }: any) {
  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 mb-6">
      <div className="text-xs uppercase tracking-wide text-gray-400 mb-4">
        {title}
      </div>
      {children}
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles =
    severity === "HIGH"
      ? "bg-red-500/10 text-red-400 border-red-500/30"
      : severity === "MEDIUM"
      ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
      : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";

  return (
    <div className={`text-xs px-3 py-1 rounded-md border ${styles}`}>
      {severity}
    </div>
  );
}

function MetricSmall({ label, value }: any) {
  return (
    <div>
      <span className="text-gray-500">{label}</span>{" "}
      <span className="text-white font-medium">{value ?? 0}</span>
    </div>
  );
}

function MetricLarge({ label, value }: any) {
  return (
    <div>
      <div className="text-2xl font-semibold text-white">
        {value ?? 0}
      </div>
      <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">
        {label}
      </div>
    </div>
  );
}