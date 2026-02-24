"use client";

import { useEffect, useState } from "react";
import GraphEditorView from "../main/GraphEditorView";

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
  const [tab, setTab] = useState<
    "impact" | "project" | "symbol"
  >("impact");

  const [projectSymbols, setProjectSymbols] = useState<any>(null);
  const [loadingProject, setLoadingProject] = useState(false);

  const [selectedSymbol, setSelectedSymbol] = useState<any>(null);
  const [loadingSymbol, setLoadingSymbol] = useState(false);


  // ---------------- Load Project Symbols ----------------
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

  // ---------------- Load Symbol Details ----------------
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
    } catch (err) {
      console.error("Failed to load symbol details");
    } finally {
      setLoadingSymbol(false);
    }
  }



  return (
    <div className="w-[380px] bg-[#252526] border-l border-[#2D2D2D] flex flex-col">

      {/* ================= Tabs ================= */}
      <div className="flex border-b border-[#2D2D2D] text-xs">
        {["impact", "project"].map((t) => (
          <button
            key={t}
            onClick={() => {
              setTab(t as any);
              setSelectedSymbol(null);

            }}
            className={`flex-1 py-2 transition ${
              tab === t
                ? "bg-[#1E1E1E] text-white border-b-2 border-blue-500"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t === "impact"
              ? "File Impact"
              : t === "project"
              ? "Project Symbols"
              : "Project Graph"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-5 text-sm">

        {/* ================= IMPACT TAB ================= */}
        {tab === "impact" && (
          <>
            {!impact ? (
              <div className="text-gray-400">
                Select a file to see impact analysis
              </div>
            ) : (
              <ImpactDetails impact={impact} />
            )}
          </>
        )}

        {/* ================= PROJECT TAB ================= */}
        {tab === "project" && (
          <>
            {loadingProject && (
              <div className="text-gray-400">Loading project symbols...</div>
            )}

            {!loadingProject && projectSymbols && (
              <>
                <Section title="Project Overview">
                  <Metric label="Total Symbols" value={projectSymbols.total_symbols} />
                  <Metric label="Avg Fan-In" value={projectSymbols.average_fan_in} />
                  <Metric label="Avg Fan-Out" value={projectSymbols.average_fan_out} />
                </Section>

                <Section title="Top Risky Symbols">
                  {(projectSymbols.top_risky_symbols || []).slice(0, 10).map((s: any) => (
                    <SymbolCard key={s.symbol} data={s} onClick={() => onOpenSymbolGraph(s.symbol)} />
                  ))}
                </Section>

                <Section title="Most Depended Symbols">
                  {(projectSymbols.most_depended_symbols || []).slice(0, 10).map((s: any) => (
                    <SymbolCard key={s.symbol} data={s} onClick={() => onOpenSymbolGraph(s.symbol)} />
                  ))}
                </Section>

                <Section title="Most Outgoing Symbols">
                  {(projectSymbols.most_outgoing_symbols || []).slice(0, 10).map((s: any) => (
                    <SymbolCard key={s.symbol} data={s} onClick={() => onOpenSymbolGraph(s.symbol)} />
                  ))}
                </Section>
              </>
            )}
          </>
        )}

        {/* ================= SYMBOL DETAIL VIEW ================= */}
        {tab === "symbol" && (
          <>
            {loadingSymbol && (
              <div className="text-gray-400">Loading symbol details...</div>
            )}

            {!loadingSymbol && selectedSymbol && (
              <>
                <button
                  onClick={() => setTab("project")}
                  className="mb-4 text-xs text-blue-400 hover:underline"
                >
                  ← Back to Project Symbols
                </button>

                <Section title="Symbol Info">
                  <div className="text-white font-semibold">
                    {selectedSymbol.name}
                  </div>
                  <div className="text-xs text-gray-400">
                    {selectedSymbol.type} | {selectedSymbol.file}
                  </div>
                </Section>

                <Section title="Signature">
                  <div className="text-xs">
                    Parameters:{" "}
                    {(selectedSymbol.parameters || [])
                      .map((p: any) => p.name)
                      .join(", ") || "None"}
                  </div>
                  <div className="text-xs">
                    Return: {selectedSymbol.return_type || "None"}
                  </div>
                </Section>

                <Section title="Risk Metrics">
                  <Metric label="Fan-In" value={selectedSymbol.fan_in} />
                  <Metric label="Fan-Out" value={selectedSymbol.fan_out} />
                  <Metric label="Blast Radius" value={selectedSymbol.blast_radius} />
                  <Metric label="Instability" value={selectedSymbol.instability} />
                  <Metric label="Severity" value={selectedSymbol.severity} />
                </Section>

                {selectedSymbol.docstring && (
                  <Section title="Documentation">
                    <div className="text-xs text-gray-300 whitespace-pre-wrap">
                      {selectedSymbol.docstring}
                    </div>
                  </Section>
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

function ImpactDetails({ impact }: any) {
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

  const severityColor =
    severity === "HIGH"
      ? "text-red-400"
      : severity === "MEDIUM"
      ? "text-yellow-400"
      : "text-green-400";

  return (
    <>
      <Section title="Impact Summary">
        <Metric label="Blast Radius" value={blast_radius ?? 0} />
        <Metric label="Direct Dependents" value={direct_dependents ?? 0} />
        <Metric label="Depends On" value={depends_on ?? 0} />
      </Section>

      <Section title="Architecture">
        <Metric label="Role" value={role ?? "-"} />
        <Metric label="Instability" value={instability ?? 0} />
        <Metric
          label="Severity"
          value={<span className={severityColor}>{severity}</span>}
        />
      </Section>

      <Section title="Impact Breakdown">
        <Metric label="Production Impact" value={production_impact ?? 0} />
        <Metric label="Test Impact" value={test_impact ?? 0} />
      </Section>

      <Section title="What This Calls">
        {calls.length === 0
          ? <Empty />
          : calls.map((file: string) => (
              <Clickable key={file}>{file}</Clickable>
            ))}
      </Section>

      <Section title="Who Calls This">
        {called_by.length === 0
          ? <Empty />
          : called_by.map((file: string) => (
              <Clickable key={file} green>
                {file}
              </Clickable>
            ))}
      </Section>
    </>
  );
}

/* ================= Shared UI Components ================= */

function Section({ title, children }: any) {
  return (
    <div className="mb-6">
      <div className="text-xs text-gray-400 uppercase mb-2">
        {title}
      </div>
      {children}
    </div>
  );
}

function Metric({ label, value }: any) {
  return (
    <div className="flex justify-between mb-1">
      <span>{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  );
}

function SymbolCard({ data, onClick }: any) {
  const severityColor =
    data.severity === "HIGH"
      ? "text-red-400"
      : data.severity === "MEDIUM"
      ? "text-yellow-400"
      : "text-green-400";

  return (
    <div
      onClick={onClick}
      className="mb-3 p-2 bg-[#2A2D2E] rounded hover:bg-[#323538] transition cursor-pointer"
    >
      <div className="flex justify-between">
        <div className="text-white text-sm">{data.name}</div>
        <div className="text-xs text-gray-400">{data.type}</div>
      </div>

      <div className="text-xs text-gray-400 mt-1">
        Fan-in: {data.fan_in} | Fan-out: {data.fan_out}
      </div>

      <div className="text-xs text-gray-400">
        Blast: {data.blast_radius} | Instability: {data.instability}
      </div>

      <div className={`text-xs mt-1 ${severityColor}`}>
        {data.severity}
      </div>
    </div>
  );
}

function Clickable({ children, green }: any) {
  return (
    <div
      className={`truncate mb-1 cursor-pointer hover:underline ${
        green ? "text-green-400" : "text-blue-400"
      }`}
    >
      {children}
    </div>
  );
}

function Empty() {
  return <div className="text-gray-500">None</div>;
}