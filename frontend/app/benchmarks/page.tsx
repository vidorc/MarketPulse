"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, Stat } from "@/components/ui/Card";
import { BarChart } from "@/components/ui/Chart";
import { Column, DataTable } from "@/components/ui/DataTable";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { api, ApiError } from "@/lib/api";
import { humanize, pct } from "@/lib/format";
import type { CategoryMetricOut } from "@/lib/types";
import { useApi } from "@/lib/useApi";
import { useState } from "react";

export default function BenchmarksPage() {
  const { data, loading, error, reload } = useApi(() => api.getBenchmarks(), []);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);

  const runSnapshot = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const res = await api.runBenchmark();
      setRunMsg(`Snapshot saved — evaluated ${res.evaluated} labelled articles.`);
      reload();
    } catch (err) {
      setRunMsg(
        err instanceof ApiError ? err.message : "Failed to run benchmark."
      );
    } finally {
      setRunning(false);
    }
  };

  const columns: Column<CategoryMetricOut>[] = [
    {
      key: "category",
      header: "Article type",
      render: (c) => (
        <span className="font-medium text-ink">{humanize(c.category)}</span>
      ),
    },
    { key: "rows", header: "Rows", align: "right", render: (c) => <span className="tnum">{c.rows}</span> },
    { key: "precision", header: "Precision", align: "right", render: (c) => <span className="tnum">{pct(c.precision)}</span> },
    { key: "recall", header: "Recall", align: "right", render: (c) => <span className="tnum">{pct(c.recall)}</span> },
    { key: "f1", header: "F1", align: "right", render: (c) => <span className="tnum text-gold">{pct(c.f1)}</span> },
    {
      key: "tpfpfn",
      header: "TP / FP / FN",
      align: "right",
      render: (c) => (
        <span className="tnum text-muted">
          {c.tp} / <span className="text-neg">{c.fp}</span> /{" "}
          <span className="text-medium">{c.fn}</span>
        </span>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Benchmark Analytics"
        subtitle="Precision, recall, F1, and accuracy against the ground-truth set."
        action={
          <Button variant="primary" onClick={runSnapshot} disabled={running}>
            {running ? "Running…" : "Run snapshot"}
          </Button>
        }
      />

      {runMsg && (
        <div className="mb-4 rounded-md border border-line bg-panel px-3 py-2 text-[12.5px] text-ink-soft">
          {runMsg}
        </div>
      )}

      {loading ? (
        <Card>
          <SkeletonRows rows={6} />
        </Card>
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data || data.evaluated === 0 ? (
        <Card>
          <EmptyState title="No scored articles yet">
            Benchmarks compare predicted tickers against the ground-truth labels
            for articles that have been ingested and processed. Seed or label
            ground truth, process the matching articles, then re-check here.
          </EmptyState>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Precision" value={pct(data.overall.precision)} accent />
            <Stat label="Recall" value={pct(data.overall.recall)} />
            <Stat label="F1 Score" value={pct(data.overall.f1)} accent />
            <Stat label="Accuracy" value={pct(data.overall.accuracy)} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader title="Confusion totals" />
              <CardBody className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <span className="text-[12px] uppercase tracking-wide text-muted">
                    Evaluated
                  </span>
                  <span className="tnum text-[15px] text-ink">
                    {data.evaluated}
                  </span>
                </div>
                <BarChart
                  data={[
                    { label: "True Positives", value: data.overall.tp, color: "var(--color-pos)" },
                    { label: "False Positives", value: data.overall.fp, color: "var(--color-neg)" },
                    { label: "False Negatives", value: data.overall.fn, color: "var(--color-medium)" },
                  ]}
                />
              </CardBody>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader title="F1 by article type" />
              <CardBody>
                {data.per_category.length === 0 ? (
                  <EmptyState title="No category data" />
                ) : (
                  <BarChart
                    data={data.per_category.map((c) => ({
                      label: humanize(c.category),
                      value: Math.round(c.f1 * 100),
                    }))}
                    valueFormatter={(v) => `${v}%`}
                  />
                )}
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader title="Per-category breakdown" />
            {data.per_category.length === 0 ? (
              <EmptyState title="No category data" />
            ) : (
              <DataTable
                columns={columns}
                rows={data.per_category}
                rowKey={(c) => c.category}
              />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
