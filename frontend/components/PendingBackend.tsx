import type { ReactNode } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";

/**
 * Placeholder for pages whose backend lands in a later phase. Deliberately shows
 * NO fabricated metrics — it states what the page will do and what it needs, so
 * the UI never misrepresents capability the platform doesn't have yet.
 */
export function PendingBackend({
  phase,
  endpoint,
  willShow,
}: {
  phase: string;
  endpoint: string;
  willShow: ReactNode[];
}) {
  return (
    <Card className="[animation:rise_0.45s_cubic-bezier(0.22,1,0.36,1)_both]">
      <CardHeader
        title="Backend pending"
        action={
          <span className="rounded-sm border border-gold/25 bg-gold/[0.06] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-gold">
            {phase}
          </span>
        }
      />
      <CardBody className="space-y-5">
        <p className="text-[13.5px] leading-relaxed text-ink-soft">
          This view is built but not yet wired to data — its backend ships in{" "}
          <span className="font-medium text-gold">{phase}</span>. We show nothing
          here rather than placeholder numbers, so the product never misrepresents
          what it can do.
        </p>

        <div>
          <div className="mb-2 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
            Will display
          </div>
          <ul className="space-y-1.5">
            {willShow.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 text-[13px] text-ink-soft"
              >
                <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-gold" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-md border border-line bg-surface px-3 py-2.5">
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
            Planned endpoint
          </div>
          <code className="tnum text-[12.5px] text-gold">{endpoint}</code>
        </div>
      </CardBody>
    </Card>
  );
}
