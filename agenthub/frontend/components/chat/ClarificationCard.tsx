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
    <div className="rounded-lg border border-gold/20 bg-gold/[0.06] p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-gold">?</span>
        <h3 className="text-sm font-display font-semibold text-gold">
          需要澄清
        </h3>
      </div>
      <p className="mb-3 text-sm text-ink/70 font-body">{question}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onSelect(option)}
            className="rounded-lg border border-gold/20 bg-gold/[0.08] px-3 py-1.5 text-sm text-gold/80 font-body transition-colors hover:bg-gold/15 hover:border-gold/30"
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
