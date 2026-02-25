"use client";

import { useEffect, useState } from "react";

interface Props {
  repoId: string;
  commitHash: string;
  selectedFile: string | null;
  impact: any;
  onOpenProjectGraph: () => void;
  onOpenSymbolGraph: (symbolId: string) => void;
}

export default function ImpactPanel({
  repoId,
  commitHash,
  selectedFile,
  impact,
  onOpenProjectGraph,
  onOpenSymbolGraph,
}: Props) {
  const [tab, setTab] = useState<"impact" | "project" | "symbol">("impact");

  const [projectSymbols, setProjectSymbols] = useState<any>(null);
  const [loadingProject, setLoadingProject] = useState(false);

  const [selectedSymbol, setSelectedSymbol] = useState<any>(null);
  const [loadingSymbol, setLoadingSymbol] = useState(false);

  // ================= Load Project Symbols =================
  useEffect(() => {
    if (tab !== "project") return;

    async function loadProjectSymbols() {
      try {
        setLoadingProject(true);
        const res = await fetch(
          `http://localhost:8000/impact/project-symbols/${repoId}/${commitHash}`
        );
        const data = await res.json();
        setProjectSymbols(data);
      } catch {
        setProjectSymbols(null);
      } finally {
        setLoadingProject(false);
      }
    }

    loadProjectSymbols();
  }, [tab, repoId, commitHash]);

  // ================= Load Symbol Details =================
  async function openSymbol(symbolId: string) {
    try {
      setLoadingSymbol(true);
      setTab("symbol");

      const res = await fetch(
        `http://localhost:8000/impact/symbol-details/${repoId}/${commitHash}?symbol_id=${encodeURIComponent(
          symbolId
        )}`
      );

      const data = await res.json();
      setSelectedSymbol(data);
    } finally {
      setLoadingSymbol(false);
    }
  }

  return (
    <div className="w-[420px] bg-[#0B1220] border-l border-[#1F2937] flex flex-col">

      {/* ================= Tabs ================= */}
      <div className="flex border-b border-[#1F2937] bg-[#0F172A] text-xs sticky top-0 z-10">
        {[
          { id: "impact", label: "File Impact" },
          { id: "project", label: "Project Symbols" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => {
              setTab(t.id as any);
              setSelectedSymbol(null);
            }}
            className={`flex-1 py-3 font-medium transition ${
              tab === t.id
                ? "text-white border-b-2 border-blue-500"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ================= Scroll Area ================= */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6 text-sm">

        {/* ================= IMPACT TAB ================= */}
        {tab === "impact" && (
          !impact ? (
            <EmptyState text="Select a file to see impact analysis" />
          ) : (
            <ImpactDetails
              impact={impact}
              onOpenSymbolGraph={onOpenSymbolGraph}
            />
          )
        )}

        {/* ================= PROJECT TAB ================= */}
        {tab === "project" && (
          <>
            {loadingProject && <Loading text="Loading project analysis..." />}

            {!loadingProject && projectSymbols && (
              <>
                <Card title="Project Overview">
                  <MetricGrid>
                    <Metric label="Total Symbols" value={projectSymbols.total_symbols} />
                    <Metric label="Avg Fan-In" value={projectSymbols.average_fan_in} />
                    <Metric label="Avg Fan-Out" value={projectSymbols.average_fan_out} />
                  </MetricGrid>
                </Card>

                <Card title="Top Risky Symbols">
                  {(projectSymbols.top_risky_symbols || [])
                    .slice(0, 8)
                    .map((s: any) => (
                      <SymbolCard key={s.symbol} data={s} onClick={() => openSymbol(s.symbol)} />
                    ))}
                </Card>

                <Card title="Most Depended Symbols">
                  {(projectSymbols.most_depended_symbols || [])
                    .slice(0, 8)
                    .map((s: any) => (
                      <SymbolCard key={s.symbol} data={s} onClick={() => openSymbol(s.symbol)} />
                    ))}
                </Card>

                <Card title="Most Outgoing Symbols">
                  {(projectSymbols.most_outgoing_symbols || [])
                    .slice(0, 8)
                    .map((s: any) => (
                      <SymbolCard key={s.symbol} data={s} onClick={() => openSymbol(s.symbol)} />
                    ))}
                </Card>
              </>
            )}
          </>
        )}

        {/* ================= SYMBOL DETAIL ================= */}
        {tab === "symbol" && (
          <>
            {loadingSymbol && <Loading text="Loading symbol details..." />}

            {!loadingSymbol && selectedSymbol && (
              <>
                <button
                  onClick={() => setTab("project")}
                  className="mb-6 text-xs text-blue-400 hover:opacity-80"
                >
                  ← Back to Project Symbols
                </button>

                <Card title="Symbol Info">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-white font-semibold text-base">
                        {selectedSymbol.name}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {selectedSymbol.type} • {selectedSymbol.file}
                      </div>
                    </div>
                    <SeverityBadge severity={selectedSymbol.severity} />
                  </div>
                </Card>

                <Card title="Signature">
                  <div className="text-gray-300 text-xs">
                    Parameters:{" "}
                    {(selectedSymbol.parameters || [])
                      .map((p: any) => `${p.name}: ${p.type || "?"}`)
                      .join(", ") || "None"}
                    <div className="mt-2">
                      Return: {selectedSymbol.return_type || "None"}
                    </div>
                  </div>
                </Card>

                <Card title="Risk Metrics">
                  <MetricGrid>
                    <Metric label="Fan-In" value={selectedSymbol.fan_in} />
                    <Metric label="Fan-Out" value={selectedSymbol.fan_out} />
                    <Metric label="Blast Radius" value={selectedSymbol.blast_radius} />
                    <Metric label="Instability" value={selectedSymbol.instability} />
                  </MetricGrid>
                </Card>

                {/* 🔥 What This Calls */}
                <Card title="What This Calls">
                  <DependencyList
                    items={selectedSymbol.calls}
                    onClick={onOpenSymbolGraph}
                    color="blue"
                  />
                </Card>

                {/* 🔥 Who Calls This */}
                <Card title="Who Calls This">
                  <DependencyList
                    items={selectedSymbol.called_by}
                    onClick={onOpenSymbolGraph}
                    color="green"
                  />
                </Card>

                {selectedSymbol.docstring && (
                  <Card title="Documentation">
                    <div className="text-xs text-gray-300 whitespace-pre-wrap">
                      {selectedSymbol.docstring}
                    </div>
                  </Card>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ================= Impact Details ================= */

function ImpactDetails({ impact, onOpenSymbolGraph }: any) {
  const {
    blast_radius,
    direct_dependents,
    depends_on,
    instability,
    role,
    severity,
    production_impact,
    test_impact,
    calls = [],
    called_by = [],
  } = impact || {};

  return (
    <>
      <Card title="Impact Summary">
        <MetricGrid>
          <Metric label="Blast Radius" value={blast_radius ?? 0} />
          <Metric label="Direct Dependents" value={direct_dependents ?? 0} />
          <Metric label="Depends On" value={depends_on ?? 0} />
        </MetricGrid>
      </Card>

      <Card title="Architecture">
        <MetricGrid>
          <Metric label="Role" value={role ?? "-"} />
          <Metric label="Instability" value={instability ?? 0} />
          <Metric
            label="Severity"
            value={<SeverityBadge severity={severity} />}
          />
        </MetricGrid>
      </Card>

      <Card title="Impact Breakdown">
        <MetricGrid>
          <Metric label="Production Impact" value={production_impact ?? 0} />
          <Metric label="Test Impact" value={test_impact ?? 0} />
        </MetricGrid>
      </Card>

      <Card title="What This Calls">
        <DependencyList items={calls} onClick={onOpenSymbolGraph} color="blue" />
      </Card>

      <Card title="Who Calls This">
        <DependencyList items={called_by} onClick={onOpenSymbolGraph} color="green" />
      </Card>
    </>
  );
}

/* ================= Shared Components ================= */

function Card({ title, children }: any) {
  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 mb-6">
      <div className="text-xs uppercase tracking-wide text-gray-400 mb-4">
        {title}
      </div>
      {children}
    </div>
  );
}

function Metric({ label, value }: any) {
  return (
    <div>
      <div className="text-lg font-semibold text-white">{value}</div>
      <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">
        {label}
      </div>
    </div>
  );
}

function MetricGrid({ children }: any) {
  return <div className="grid grid-cols-2 gap-4">{children}</div>;
}

function DependencyList({ items = [], onClick, color }: any) {
  if (!items || items.length === 0) {
    return <div className="text-gray-500 text-xs">None</div>;
  }

  const baseColor =
    color === "green"
      ? "hover:bg-green-500/10 text-green-400"
      : "hover:bg-blue-500/10 text-blue-400";

  return (
    <div className="space-y-2">
      {items.map((item: string) => (
        <div
          key={item}
          onClick={() => onClick?.(item)}
          className={`truncate px-3 py-2 rounded-md text-xs cursor-pointer transition ${baseColor}`}
        >
          {item}
        </div>
      ))}
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
    <div className={`text-xs px-2 py-1 rounded-md border ${styles}`}>
      {severity}
    </div>
  );
}

function Loading({ text }: any) {
  return <div className="text-gray-400">{text}</div>;
}

function EmptyState({ text }: any) {
  return <div className="text-gray-500">{text}</div>;
}

function SymbolCard({ data, onClick }: any) {
  return (
    <div
      onClick={onClick}
      className="p-3 mb-3 bg-[#111827] border border-[#1F2937]
                 rounded-lg cursor-pointer
                 hover:border-blue-500/40
                 hover:bg-[#162036]
                 transition-all duration-200"
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="text-white text-sm font-medium">
            {data.name}
          </div>
          <div className="text-xs text-gray-400 mt-1 uppercase tracking-wide">
            {data.type}
          </div>
        </div>

        <SeverityBadge severity={data.severity} />
      </div>

      <div className="mt-3 text-xs text-gray-400">
        Fan-in: <span className="text-white">{data.fan_in ?? 0}</span> •
        Fan-out: <span className="text-white ml-1">{data.fan_out ?? 0}</span>
      </div>

      <div className="text-xs text-gray-400">
        Blast: <span className="text-white">{data.blast_radius ?? 0}</span> •
        Instability: <span className="text-white ml-1">{data.instability ?? 0}</span>
      </div>
    </div>
  );
}