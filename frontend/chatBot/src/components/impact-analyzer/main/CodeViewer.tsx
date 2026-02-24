interface Props {
  content: string;
}

export default function CodeViewer({ content }: Props) {
  if (!content) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1E1E1E] text-gray-500">
        Select a file to view content
      </div>
    );
  }

  const lines = content.split("\n");

  return (
    <div className="flex-1 overflow-auto bg-[#1E1E1E] font-mono text-sm">

      {/* This wrapper forces true horizontal expansion */}
      <div className="inline-block min-w-full p-4">

        {lines.map((line, i) => (
          <div key={i} className="flex hover:bg-[#2A2D2E]">

            {/* Line Numbers */}
            <span className="w-12 text-right pr-4 text-[#858585] select-none shrink-0">
              {i + 1}
            </span>

            {/* Code Line */}
            <span className="whitespace-pre text-gray-200">
              {line}
            </span>

          </div>
        ))}

      </div>
    </div>
  );
}