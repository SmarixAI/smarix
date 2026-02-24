import { FileNode } from "@/app/impact-analyzer/types";

export default function HighRiskSymbols({ files }: { files: FileNode[] }) {
  const symbols = files.flatMap((f) => f.symbols);

  return (
    <div className="mt-6">
      <h3 className="text-xs uppercase text-yellow-400 mb-2">High Risk Symbols</h3>
      {symbols.map((s) => (
        <div key={s} className="text-sm text-yellow-300">
          {s}
        </div>
      ))}
    </div>
  );
}