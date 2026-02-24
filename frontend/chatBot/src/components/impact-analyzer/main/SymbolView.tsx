"use client";

import { useState } from "react";

interface Props {
  fileSymbols: any;
}

export default function SymbolView({ fileSymbols }: Props) {
  const [selectedSymbol, setSelectedSymbol] = useState<any>(null);

  if (!fileSymbols) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1E1E1E] text-gray-500">
        Select a file to inspect symbols
      </div>
    );
  }

  // ================= LIST VIEW =================
  if (!selectedSymbol) {
    return (
      <div className="flex-1 overflow-y-auto bg-[#1E1E1E] p-6 text-sm">

        <div className="text-lg text-white mb-4">
          File Symbols ({fileSymbols.total_symbols})
        </div>

        {fileSymbols.symbols.map((s: any) => (
          <div
            key={s.symbol}
            onClick={() => setSelectedSymbol(s)}
            className="mb-3 p-3 bg-[#252526] rounded cursor-pointer hover:bg-[#2A2D2E] transition"
          >
            <div className="flex justify-between">
              <div className="text-white font-medium">
                {s.name}
              </div>
              <div className="text-xs text-gray-400">
                {s.type}
              </div>
            </div>

            <div className="text-xs text-gray-400 mt-1">
              Fan-in: {s.fan_in} | Blast: {s.blast_radius}
            </div>

            <div className={`text-xs mt-1 ${
              s.severity === "HIGH"
                ? "text-red-400"
                : s.severity === "MEDIUM"
                ? "text-yellow-400"
                : "text-green-400"
            }`}>
              {s.severity}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // ================= DETAIL VIEW =================
  return (
    <div className="flex-1 overflow-y-auto bg-[#1E1E1E] p-6 text-sm">

      <button
        onClick={() => setSelectedSymbol(null)}
        className="text-xs text-blue-400 mb-4 hover:underline"
      >
        ← Back to file symbols
      </button>

      <div className="text-lg text-white mb-4">
        {selectedSymbol.name}
      </div>

      <div className="mb-4">
        <div className="text-gray-400 text-xs mb-1">Signature</div>
        <div>
          Parameters:{" "}
          {selectedSymbol.parameters.length === 0
            ? "None"
            : selectedSymbol.parameters.map((p: any) => p.name).join(", ")}
        </div>
        <div>Return: {selectedSymbol.return_type || "None"}</div>
      </div>

      <div className="mb-4">
        <div className="text-gray-400 text-xs mb-1">Risk</div>
        <div>Fan-in: {selectedSymbol.fan_in}</div>
        <div>Fan-out: {selectedSymbol.fan_out}</div>
        <div>Blast Radius: {selectedSymbol.blast_radius}</div>
      </div>

      {selectedSymbol.docstring && (
        <div>
          <div className="text-gray-400 text-xs mb-1">Documentation</div>
          <div className="whitespace-pre-wrap text-gray-400">
            {selectedSymbol.docstring}
          </div>
        </div>
      )}
    </div>
  );
}