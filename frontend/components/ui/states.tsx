import type { ReactNode } from "react";
import { Button } from "./Button";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-10 text-muted">
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-gold/60 opacity-75 [animation:pulse-dot_2s_ease-in-out_infinite]" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-gold" />
      </span>
      <span className="text-[12px] uppercase tracking-[0.14em]">{label}…</span>
    </div>
  );
}

/** Shimmering skeleton rows for first-paint loading of tables/cards. */
export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton h-9 w-full rounded-md" />
      ))}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="m-4 space-y-3 rounded-lg border border-neg/30 bg-neg/[0.06] px-4 py-6">
      <div className="flex items-center gap-2 text-[12px] font-medium uppercase tracking-[0.12em] text-neg">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-neg" />
        Request failed
      </div>
      <p className="text-[13px] text-ink-soft">{message}</p>
      {onRetry && (
        <Button variant="subtle" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="m-4 rounded-lg border border-dashed border-line px-4 py-12 text-center">
      <div className="text-[12px] font-medium uppercase tracking-[0.14em] text-muted">
        {title}
      </div>
      {children && (
        <div className="mx-auto mt-2 max-w-sm text-[13px] text-muted/80">
          {children}
        </div>
      )}
    </div>
  );
}
