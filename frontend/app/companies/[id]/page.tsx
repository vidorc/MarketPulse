"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, Stat } from "@/components/ui/Card";
import { StackedBar } from "@/components/ui/Chart";
import { ErrorState, Loading } from "@/components/ui/states";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#34d399",
  neutral: "#8b97a8",
  negative: "#f8717a",
};

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  const { data, loading, error, reload } = useApi(
    () => api.getCompany(id),
    [id]
  );

  return (
    <div>
      <PageHeader
        title="Company Explorer"
        subtitle="Aliases, recent mentions, and sentiment trend."
        action={
          <Link href="/companies">
            <Button variant="subtle">← All companies</Button>
          </Link>
        }
      />

      {loading ? (
        <Loading label="Loading company" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data ? null : (
        <div className="space-y-5 [animation:fade-in_0.4s_ease-out_both]">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold tracking-tight text-ink">
              {data.canonical_name}
            </h2>
            {data.ticker && <Badge value={data.ticker} />}
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <Stat label="Total mentions" value={data.mention_count} accent />
            <Stat label="Aliases" value={data.aliases.length} />
            <Stat label="Recent items" value={data.recent_mentions.length} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader title="Recent mentions" />
              <CardBody className="space-y-2">
                {data.recent_mentions.length === 0 ? (
                  <p className="py-3 text-[12.5px] text-muted">No mentions yet.</p>
                ) : (
                  data.recent_mentions.map((m) => (
                    <Link
                      key={m.article_id}
                      href={`/articles/${m.article_id}`}
                      className="flex items-start justify-between gap-3 rounded-md border border-line bg-surface px-3 py-2.5 transition-colors hover:border-line-bright hover:bg-panel-2"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-[12.5px] font-medium text-ink">
                          {m.title}
                        </div>
                        <div className="tnum mt-0.5 text-[10.5px] text-muted">
                          {formatDate(m.created_at)}
                        </div>
                      </div>
                      {m.sentiment && (
                        <Badge kind="sentiment" value={m.sentiment} />
                      )}
                    </Link>
                  ))
                )}
              </CardBody>
            </Card>

            <div className="space-y-4">
              <Card>
                <CardHeader title="Sentiment trend" />
                <CardBody>
                  {data.sentiment_trend.length === 0 ? (
                    <p className="py-3 text-[12.5px] text-muted">
                      No sentiment data yet.
                    </p>
                  ) : (
                    <StackedBar
                      segments={data.sentiment_trend.map((s) => ({
                        label: s.label,
                        value: s.count,
                        color:
                          SENTIMENT_COLORS[s.label.toLowerCase()] ?? "#8b97a8",
                      }))}
                    />
                  )}
                </CardBody>
              </Card>

              <Card>
                <CardHeader title="Aliases" />
                <CardBody>
                  {data.aliases.length === 0 ? (
                    <p className="text-[12.5px] text-muted">
                      No aliases registered.
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {data.aliases.map((a) => (
                        <span
                          key={`${a.alias_text}-${a.source}`}
                          className="inline-flex items-center gap-1 rounded-sm border border-line bg-surface px-1.5 py-0.5 text-[11px] text-ink-soft"
                          title={`source: ${a.source}`}
                        >
                          {a.alias_text}
                          <span className="text-[9px] uppercase text-faint">
                            {a.source}
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
