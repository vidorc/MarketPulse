"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Column, DataTable } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { api } from "@/lib/api";
import { formatDateShort, humanize, truncate } from "@/lib/format";
import { ARTICLE_TYPES, ArticleSummary } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const PAGE = 25;

const INPUT =
  "rounded-md border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

export default function FeedPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");

  const { data, loading, error, reload } = useApi(
    () =>
      api.listArticles({
        limit: PAGE,
        offset,
        search: search || undefined,
        article_type: type || undefined,
        status: status || undefined,
      }),
    [offset, search, type, status]
  );

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setSearch(searchInput.trim());
  };

  const columns: Column<ArticleSummary>[] = [
    {
      key: "title",
      header: "Headline",
      render: (a) => (
        <div className="max-w-xl">
          <div className="font-medium text-ink">{truncate(a.title, 110)}</div>
          {a.source && (
            <div className="mt-0.5 text-[11px] text-muted">{a.source}</div>
          )}
        </div>
      ),
    },
    {
      key: "type",
      header: "Type",
      render: (a) =>
        a.article_type ? (
          <Badge kind="type" value={humanize(a.article_type)} />
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    {
      key: "tickers",
      header: "Tickers",
      render: (a) =>
        a.tickers.length ? (
          <div className="flex flex-wrap gap-1">
            {a.tickers.slice(0, 4).map((t) => (
              <Badge key={t} value={t} />
            ))}
            {a.tickers.length > 4 && (
              <span className="text-[11px] text-muted">
                +{a.tickers.length - 4}
              </span>
            )}
          </div>
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    {
      key: "impact",
      header: "Impact",
      align: "center",
      render: (a) =>
        a.impact ? (
          <Badge kind="impact" value={a.impact} />
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    {
      key: "conf",
      header: "Conf",
      align: "right",
      render: (a) => (
        <span className="tnum text-ink-soft">
          {a.confidence != null ? a.confidence : "—"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      align: "center",
      render: (a) => <Badge kind="status" value={a.status} />,
    },
    {
      key: "date",
      header: "Date",
      align: "right",
      render: (a) => (
        <span className="tnum text-muted">{formatDateShort(a.created_at)}</span>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="News Feed"
        subtitle="Processed financial news with extracted companies, tickers, and impact."
      />

      <Card className="mb-4">
        <form
          onSubmit={submitSearch}
          className="flex flex-wrap items-center gap-2 p-2.5"
        >
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search headlines…"
            className={`min-w-[240px] flex-1 ${INPUT}`}
          />
          <select
            value={type}
            onChange={(e) => {
              setOffset(0);
              setType(e.target.value);
            }}
            className={INPUT}
          >
            <option value="">All types</option>
            {ARTICLE_TYPES.map((t) => (
              <option key={t} value={t}>
                {humanize(t)}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => {
              setOffset(0);
              setStatus(e.target.value);
            }}
            className={INPUT}
          >
            <option value="">All status</option>
            <option value="processed">Processed</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </form>
      </Card>

      <Card>
        {loading ? (
          <SkeletonRows rows={8} />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No articles yet">
            Upload a CSV from the Upload page to populate the feed.
          </EmptyState>
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.items}
              rowKey={(a) => a.id}
              onRowClick={(a) => router.push(`/articles/${a.id}`)}
            />
            <div className="border-t border-line">
              <Pagination
                total={data.total}
                limit={PAGE}
                offset={offset}
                onChange={setOffset}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
