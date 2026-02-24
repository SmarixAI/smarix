interface Props {
  onClick: () => void;
  active?: boolean;
}

export default function GraphButton({ onClick, active }: Props) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-3 py-1.5 text-xs rounded
        border transition-all duration-150
        ${
          active
            ? "bg-purple-600 border-purple-400 text-white shadow-md"
            : "bg-[#2D2D2D] border-transparent text-gray-300 hover:bg-[#3A3D41]"
        }
      `}
    >
      📊 <span>Graph</span>
    </button>
  );
}