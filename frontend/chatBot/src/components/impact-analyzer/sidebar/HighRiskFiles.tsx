import { FileNode } from "@/app/impact-analyzer/types";

interface Props {
  files: FileNode[];
  onSelectFile: (file: FileNode) => void;
}

export default function HighRiskFiles({ files, onSelectFile }: Props) {
  const highRisk = files.filter((f) => f.riskScore > 80);

  return (
    <div className="mt-6">
      <h3 className="text-xs uppercase text-red-400 mb-2">High Risk Files</h3>
      {highRisk.map((file) => (
        <div
          key={file.id}
          onClick={() => onSelectFile(file)}
          className="text-sm text-red-300 cursor-pointer"
        >
          {file.name} ({file.riskScore})
        </div>
      ))}
    </div>
  );
}