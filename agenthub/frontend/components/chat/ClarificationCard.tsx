"use client";

interface ClarificationCardProps {
  question: string;
  options: string[];
  onSelect: (option: string) => void;
}

export function ClarificationCard({
  question,
  options,
  onSelect,
}: ClarificationCardProps) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-amber-600">?</span>
        <h3 className="text-sm font-semibold text-amber-800">需要澄清</h3>
      </div>
      <p className="mb-3 text-sm text-amber-900">{question}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onSelect(option)}
            className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-sm text-amber-700 transition-colors hover:bg-amber-100"
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
