import clsx from "@/lib/clsx";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-lg border border-line bg-panel shadow-panel",
        hover &&
          "transition-all duration-200 hover:border-line-bright hover:shadow-lift",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  action,
  className,
}: {
  title: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "flex items-center justify-between border-b border-line px-4 py-2.5",
        className
      )}
    >
      <h2 className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted">
        {title}
      </h2>
      {action}
    </div>
  );
}

export function CardBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={clsx("p-4", className)}>{children}</div>;
}

/** Hero stat block — gradient surface, big mono numeral, optional delta hint. */
export function Stat({
  label,
  value,
  hint,
  accent,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: boolean;
  icon?: ReactNode;
}) {
  return (
    <div
      className={clsx(
        "group relative overflow-hidden rounded-lg border border-line bg-gradient-to-br from-panel to-surface p-4 shadow-panel transition-all duration-200 hover:border-line-bright hover:shadow-lift"
      )}
    >
      {/* Accent corner glow. */}
      <div
        className={clsx(
          "pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full blur-2xl transition-opacity duration-300",
          accent ? "bg-gold/20" : "bg-azure/10",
          "opacity-60 group-hover:opacity-100"
        )}
      />
      <div className="relative flex items-start justify-between">
        <div className="text-[10.5px] font-medium uppercase tracking-[0.14em] text-muted">
          {label}
        </div>
        {icon && <div className="text-muted">{icon}</div>}
      </div>
      <div
        className={clsx(
          "tnum relative mt-2 text-[26px] font-semibold leading-none",
          accent ? "text-gold-gradient" : "text-ink"
        )}
      >
        {value}
      </div>
      {hint && (
        <div className="relative mt-1.5 text-[11px] text-muted">{hint}</div>
      )}
    </div>
  );
}
