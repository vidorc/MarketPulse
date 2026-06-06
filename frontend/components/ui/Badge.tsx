import clsx from "@/lib/clsx";

type BadgeKind = "sentiment" | "impact" | "status" | "type" | "neutral";

const SENTIMENT: Record<string, string> = {
  positive: "border-pos/30 text-pos bg-pos/10",
  negative: "border-neg/30 text-neg bg-neg/10",
  neutral: "border-neu/30 text-neu bg-neu/10",
};

const IMPACT: Record<string, string> = {
  high: "border-high/30 text-high bg-high/10",
  medium: "border-medium/30 text-medium bg-medium/10",
  low: "border-low/30 text-low bg-low/10",
};

const STATUS: Record<string, string> = {
  processed: "border-pos/30 text-pos bg-pos/10",
  pending: "border-medium/30 text-medium bg-medium/10",
  queued: "border-medium/30 text-medium bg-medium/10",
  running: "border-gold/30 text-gold bg-gold/10",
  completed: "border-pos/30 text-pos bg-pos/10",
  failed: "border-neg/30 text-neg bg-neg/10",
};

function classesFor(kind: BadgeKind, value: string): string {
  const v = value.toLowerCase();
  if (kind === "sentiment") return SENTIMENT[v] ?? SENTIMENT.neutral;
  if (kind === "impact") return IMPACT[v] ?? IMPACT.low;
  if (kind === "status") return STATUS[v] ?? "border-line text-muted bg-panel-2";
  if (kind === "type") return "border-gold/25 text-gold bg-gold/[0.06]";
  return "border-line text-muted bg-panel-2";
}

export function Badge({
  kind = "neutral",
  value,
  label,
  className,
}: {
  kind?: BadgeKind;
  value: string;
  label?: string;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-wider whitespace-nowrap",
        classesFor(kind, value),
        className
      )}
    >
      {label ?? value}
    </span>
  );
}
