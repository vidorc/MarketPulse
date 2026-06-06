"use client";

import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader, Stat } from "@/components/ui/Card";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { api } from "@/lib/api";
import { pct } from "@/lib/format";
import type { FalseItemOut } from "@/lib/types";
import { useApi } from "@/lib/useApi";

function TickerList({ items, tone }: { items: string[]; tone: "pos" | "neg" }) {
  if (items.length === 0) return <span className="text-faint">—</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((t) => (
        <span
          key={t}
          className={
            tone === "neg"
              ? "rounded-sm border border-neg/30 bg-neg/10 px-1.5 py-0.5 font-mono text-[10.5px] uppercase text-neg"
              : "rounded-sm border border-pos/30 bg-pos/10 px-1.5 py-0.5 font-mono text-[10.5px] uppercase text-pos"
          }
        >
          {t}
        </span>
      ))}
    </div>
  );
}

function FalseList({
  title,
  hint,
  items,
  highlight,
}: {
  title: string;
  hint: string;
  items: FalseItemOut[];
  highlight: "fp" | "fn";
}) {
  const router = useRouter();
  return (
    <Card>
      <CardHeader
        title={title}
        action={<span className="text-[11px] text-muted">{items.length}</span>}
      />
      {items.length === 0 ? (
        <EmptyState title="None — clean on this axis" />
      ) : (
        <CardBody className="space-y-2.5">
          <p className="text-[11.5px] text-muted">{hint}</p>
          {items.map((f, i) => (
            <button
              key={`${f.title}-${i}`}
              onClick={() =>
                f.article_id && router.push(`/articles/${f.article_id}`)
              }
              disabled={!f.article_id}
              className="w-full rounded-md border border-line bg-surface p-3 text-left transition-colors hover:border-line-bright disabled:cursor-default"
            >
              <div className="mb-2 text-[12.5px] font-medium text-ink">
                {f.title}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="mb-1 text-[9.5px] uppercase tracking-wider text-faint">
                    Predicted
                  </div>
                  <TickerList
                    items={f.predicted}
                    tone={highlight === "fp" ? "neg" : "pos"}
                  />
                </div>
                <div>
                  <div className="mb-1 text-[9.5px] uppercase tracking-wider text-faint">
                    Expected
                  </div>
                  <TickerList
                    items={f.expected}
                    tone={highlight === "fn" ? "neg" : "pos"}
                  />
                </div>
              </div>
            </button>
          ))}
        </CardBody>
      )}
    </Card>
  );
}

export default function PerformancePage() {
  const { data, loading, error, reload } = useApi(() => api.getBenchmarks(), []);

  return (
    <div>
      <PageHeader
        title="Model Performance"
        subtitle="False-positive / false-negative analysis against ground truth."
      />

      {loading ? (
        <Card>
          <SkeletonRows rows={6} />
        </Card>
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data || data.evaluated === 0 ? (
        <Card>
          <EmptyState title="No scored articles yet">
            Once ground-truth labels match processed articles, the
            false-positive and false-negative breakdowns appear here with
            drill-through into article review.
          </EmptyState>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <Stat
              label="False Positives"
              value={data.overall.fp}
              hint="Predicted tickers that were wrong"
            />
            <Stat
              label="False Negatives"
              value={data.overall.fn}
              hint="Expected tickers the model missed"
            />
            <Stat
              label="F1 Score"
              value={pct(data.overall.f1)}
              accent
              hint={`${data.evaluated} articles evaluated`}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <FalseList
              title="False positives"
              hint="The model tagged tickers that ground truth does not include. Red = the spurious predictions."
              items={data.false_positives}
              highlight="fp"
            />
            <FalseList
              title="False negatives"
              hint="Ground truth expects tickers the model did not return. Red = the missed expectations."
              items={data.false_negatives}
              highlight="fn"
            />
          </div>
        </div>
      )}
    </div>
  );
}
