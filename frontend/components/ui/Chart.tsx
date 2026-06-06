import clsx from "@/lib/clsx";

export interface BarDatum {
  label: string;
  value: number;
  /** Optional explicit color (CSS value). Falls back to the gold accent. */
  color?: string;
}

/**
 * Horizontal bar chart rendered with plain divs — no charting dependency, which
 * keeps the build lean. Bars use a gradient fill and animate their width in.
 */
export function BarChart({
  data,
  valueFormatter = (v) => String(v),
  className,
}: {
  data: BarDatum[];
  valueFormatter?: (v: number) => string;
  className?: string;
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className={clsx("space-y-2.5", className)}>
      {data.map((d) => {
        const color = d.color ?? "var(--color-gold)";
        return (
          <div key={d.label} className="group space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="truncate pr-2 tracking-wide text-ink-soft">
                {d.label}
              </span>
              <span className="tnum shrink-0 text-muted">
                {valueFormatter(d.value)}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface ring-hairline">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${(d.value / max) * 100}%`,
                  minWidth: d.value > 0 ? "3px" : "0",
                  background: `linear-gradient(90deg, ${color}, color-mix(in srgb, ${color} 70%, white))`,
                  boxShadow: `0 0 12px -2px ${color}`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Single stacked horizontal bar showing how a total splits across segments. */
export function StackedBar({
  segments,
}: {
  segments: { label: string; value: number; color: string }[];
}) {
  const total = segments.reduce((a, s) => a + s.value, 0) || 1;
  return (
    <div className="space-y-3">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-surface ring-hairline">
        {segments.map((s) => (
          <div
            key={s.label}
            className="h-full transition-all duration-500"
            style={{
              width: `${(s.value / total) * 100}%`,
              backgroundColor: s.color,
            }}
            title={`${s.label}: ${s.value}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5 text-[11px]">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: s.color }}
            />
            <span className="uppercase tracking-wide text-muted">{s.label}</span>
            <span className="tnum text-ink-soft">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
