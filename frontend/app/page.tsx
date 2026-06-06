"use client";

import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader, Stat } from "@/components/ui/Card";
import { BarChart, StackedBar } from "@/components/ui/Chart";
import { ErrorState, Loading } from "@/components/ui/states";
import { api } from "@/lib/api";
import { humanize, pct } from "@/lib/format";
import type { AnalyticsOverview, BenchmarkResponse } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const IMPACT_COLORS: Record<string, string> = {
  high: "#f8717a",
  medium: "#fbbf57",
  low: "#34d399",
};

/**
 * The Dashboard reads server-side aggregations from /analytics (totals,
 * distributions, top companies) and real precision/recall/F1 from /benchmarks —
 * no client-side sampling or fabricated numbers.
 */
export default function DashboardPage() {
  const analyticsQ = useApi(() => api.getAnalytics(), []);
  const benchQ = useApi(() => api.getBenchmarks(), []);

  const loading = analyticsQ.loading;
  const error = analyticsQ.error;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Live overview of the extraction pipeline and benchmark quality."
      />

      {loading ? (
        <Loading label="Loading dashboard" />
      ) : error ? (
        <ErrorState message={error} onRetry={analyticsQ.reload} />
      ) : analyticsQ.data ? (
        <DashboardBody analytics={analyticsQ.data} bench={benchQ.data} />
      ) : null}
    </div>
  );
}

function DashboardBody({
  analytics,
  bench,
}: {
  analytics: AnalyticsOverview;
  bench: BenchmarkResponse | null;
}) {
  const typeData = analytics.article_types
    .map((t) => ({ label: humanize(t.label), value: t.count }))
    .slice(0, 8);

  const impactByLabel = new Map(
    analytics.impact_distribution.map((d) => [d.label, d.count])
  );
  const impactSegments = (["high", "medium", "low"] as const).map((k) => ({
    label: k,
    value: impactByLabel.get(k) ?? 0,
    color: IMPACT_COLORS[k],
  }));

  const companyData = analytics.top_companies.map((c) => ({
    label: c.ticker ? `${c.name} (${c.ticker})` : c.name,
    value: c.mentions,
  }));

  const hasBench = bench && bench.evaluated > 0;

  return (
    <div className="space-y-5 [animation:fade-in_0.4s_ease-out_both]">
      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Articles"
          value={analytics.total_articles.toLocaleString()}
          accent
          hint={`${analytics.processed_articles} processed · ${analytics.failed_articles} failed`}
        />
        <Stat
          label="Companies tracked"
          value={analytics.total_companies.toLocaleString()}
          hint={`${analytics.companies_tagged} mentioned`}
        />
        <Stat
          label="Avg confidence"
          value={
            analytics.avg_confidence > 0
              ? analytics.avg_confidence.toFixed(0)
              : "—"
          }
          hint={`${analytics.total_runs} processing runs`}
        />
        {hasBench ? (
          <Stat
            label="Precision / Recall / F1"
            value={
              <span className="text-[18px]">
                {pct(bench!.overall.precision, 0)} /{" "}
                {pct(bench!.overall.recall, 0)} /{" "}
                <span className="text-gold-gradient">
                  {pct(bench!.overall.f1, 0)}
                </span>
              </span>
            }
            hint={`${bench!.evaluated} articles vs ground truth`}
          />
        ) : (
          <div className="relative overflow-hidden rounded-lg border border-line bg-gradient-to-br from-panel to-surface p-4 shadow-panel">
            <div className="text-[10.5px] font-medium uppercase tracking-[0.14em] text-muted">
              Precision / Recall / F1
            </div>
            <div className="mt-2 text-[14px] font-medium text-muted">
              No scored articles yet
            </div>
            <Link
              href="/benchmarks"
              className="mt-1.5 inline-block text-[11px] font-medium text-gold transition-opacity hover:opacity-80"
            >
              Open benchmarks →
            </Link>
          </div>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Article types" />
          <CardBody>
            {typeData.length === 0 ? (
              <p className="py-4 text-[12px] text-muted">
                No classified articles yet.
              </p>
            ) : (
              <BarChart data={typeData} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Impact distribution" />
          <CardBody>
            {analytics.total_articles === 0 ? (
              <p className="py-4 text-[12px] text-muted">No data yet.</p>
            ) : (
              <StackedBar segments={impactSegments} />
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Top mentioned companies"
          action={
            <Link
              href="/companies"
              className="text-[11px] font-medium text-gold transition-opacity hover:opacity-80"
            >
              View all →
            </Link>
          }
        />
        <CardBody>
          {companyData.length === 0 ? (
            <p className="py-4 text-[12px] text-muted">
              No company mentions yet. Process a CSV to populate this.
            </p>
          ) : (
            <BarChart data={companyData} />
          )}
        </CardBody>
      </Card>
    </div>
  );
}
