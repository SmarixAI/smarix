"use client";

import { useState } from "react";

interface Props {
  contextData: any;
}

export default function PromptRightSidebar({ contextData }: Props) {
  const [expandedFile, setExpandedFile] = useState<string | null>(null);

  if (!contextData) {
    return (
      <div className="w-[380px] bg-[#0B1220] border-l border-[#1F2937] flex flex-col">
        <div className="px-5 py-4 border-b border-[#1F2937] bg-[#0F172A]">
          <div className="text-sm font-semibold text-white">
            Architecture Context
          </div>
        </div>

        <div className="flex-1 p-5 text-sm text-gray-400">
          Generate prompt to see architectural context.
        </div>
      </div>
    );
  }

  const {
    classification,
    file_graph,
    architecture_summary,
    structured_context,
    impact_summary,
  } = contextData;

  return (
    <div className="w-[420px] bg-[#0B1220] border-l border-[#1F2937] flex flex-col">

      {/* ================= Header ================= */}
      <div className="px-5 py-4 border-b border-[#1F2937] bg-[#0F172A]">
        <div className="text-sm font-semibold text-white">
          Architecture Intelligence
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-8 text-sm">

        {/* ================= Classification ================= */}
        <section>
          <div className="text-gray-400 mb-2">Request Classification</div>
          <div className="text-white text-xs">
            Intent: {classification?.intent}
          </div>
          <div className="text-white text-xs">
            Scope: {classification?.scope}
          </div>
          {classification?.related_files?.length > 0 && (
            <div className="text-gray-300 text-xs mt-2">
              Related:
              {classification.related_files.map((f: string) => (
                <div key={f} className="ml-2">• {f}</div>
              ))}
            </div>
          )}
        </section>

        {/* ================= Impact Summary ================= */}
        <section>
          <div className="text-gray-400 mb-2">Impact Summary</div>
          <div className="text-white text-xs">
            Total Files: {impact_summary?.total_files}
          </div>
          <div className="text-white text-xs">
            Total LOC: {impact_summary?.total_loc}
          </div>
        </section>

        {/* ================= Architecture Summary ================= */}
        <section>
          <div className="text-gray-400 mb-2">Architecture Summary</div>

          <div className="text-white text-xs">Entry Points:</div>
          {architecture_summary?.entry_points?.map((ep: string) => (
            <div key={ep} className="ml-2 text-gray-300 text-xs">
              • {ep}
            </div>
          ))}

          <div className="text-white text-xs mt-3">Core Modules:</div>
          {architecture_summary?.core_modules?.length === 0 && (
            <div className="ml-2 text-gray-500 text-xs">
              None detected
            </div>
          )}
        </section>


        {/* ================= File Graph ================= */}
        <section>
        <div className="text-gray-400 mb-2">File Dependency Graph</div>

        {/* Horizontal Scroll Container */}
        <div className="overflow-x-auto">

            <div className="space-y-2 min-w-max">

            {file_graph?.edges?.map((edge: any, i: number) => (
                <div key={i} className="text-xs flex items-center gap-3 whitespace-nowrap">

                {/* FROM */}
                <span className="text-blue-400 font-medium">
                    {edge.from}
                </span>

                {/* Arrow (stacked vertically like you want) */}
                <span className="text-gray-500">
                    →
                </span>

                {/* TO */}
                <span className="text-green-400 font-medium">
                    {edge.to}
                </span>

                </div>
            ))}

            </div>

        </div>
        </section>

        {/* ================= Structured Context ================= */}
        <section>
          <div className="text-gray-400 mb-3">
            Impacted Files ({structured_context?.length}) [Click any to expand]
          </div>

          {structured_context?.map((file: any) => {
            const isOpen = expandedFile === file.file_path;

            return (
              <div
                key={file.file_path}
                onClick={() =>
                    setExpandedFile(isOpen ? null : file.file_path)
                }
                className="bg-[#111827] p-3 rounded-lg mb-3 cursor-pointer hover:bg-[#1A2333] transition-colors"
                >
                <div className="text-white text-xs font-semibold">
                    {file.file_path}
                </div>

                <div className="text-gray-400 text-xs mt-1">
                  Role: {file.role}
                </div>

                <div className="text-gray-400 text-xs">
                  LOC: {file.metrics.loc}
                </div>

                <div className="text-gray-400 text-xs">
                  Fan-In: {file.metrics.fan_in}
                </div>

                <div className="text-gray-400 text-xs">
                  Fan-Out: {file.metrics.fan_out}
                </div>

                <div className="text-gray-400 text-xs">
                  Sensitivity: {file.metrics.sensitivity_score}
                </div>

                {/* Expandable Deep Info */}
                {isOpen && (
                  <div className="mt-3 space-y-3 text-xs">

                    {/* Imports */}
                    {file.imports?.length > 0 && (
                      <div>
                        <div className="text-gray-400">Imports:</div>
                        {file.imports.map((imp: string, i: number) => (
                          <div key={i} className="text-gray-300 ml-2">
                            • {imp}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Structure */}
                    {file.structure?.length > 0 && (
                      <div>
                        <div className="text-gray-400">Symbols:</div>
                        {file.structure.map((sym: any) => (
                          <div key={sym.symbol_id} className="ml-2 text-gray-300">
                            • {sym.type} {sym.name}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Symbol Graph */}
                    {file.symbol_graph?.length > 0 && (
                      <div>
                        <div className="text-gray-400">Call Graph:</div>
                        {file.symbol_graph.map((sg: any) => (
                          <div key={sg.symbol} className="ml-2 text-gray-300">
                            {sg.symbol}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Code Slice */}
                    <div>
                      <div className="text-gray-400">Code Preview:</div>
                      <pre className="bg-black/40 p-2 rounded text-[10px] overflow-x-auto">
                        {file.code_slice}
                      </pre>
                    </div>

                  </div>
                )}
              </div>
            );
          })}
        </section>

      </div>
    </div>
  );
}