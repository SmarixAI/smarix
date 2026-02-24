export default function ImpactAnalyzerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="h-screen w-screen bg-[#0E1B2E] text-white overflow-hidden">
      {children}
    </div>
  );
}