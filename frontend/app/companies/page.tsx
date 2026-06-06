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
import { CompanySummary } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const PAGE = 30;

const INPUT =
  "w-full rounded-md border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

export default function CompaniesPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, loading, error, reload } = useApi(
    () =>
      api.listCompanies({
        limit: PAGE,
        offset,
        search: search || undefined,
      }),
    [offset, search]
  );

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setSearch(searchInput.trim());
  };

  const columns: Column<CompanySummary>[] = [
    {
      key: "name",
      header: "Company",
      render: (c) => <span className="font-medium text-ink">{c.canonical_name}</span>,
    },
    {
      key: "ticker",
      header: "Ticker",
      render: (c) =>
        c.ticker ? (
          <Badge value={c.ticker} />
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    {
      key: "mentions",
      header: "Mentions",
      align: "right",
      render: (c) => <span className="tnum text-ink-soft">{c.mention_count}</span>,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Company Explorer"
        subtitle="NSE-listed companies in the registry, ranked by news mentions."
      />

      <Card className="mb-4">
        <form onSubmit={submit} className="flex gap-2 p-2.5">
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search company or ticker…"
            className={INPUT}
          />
        </form>
      </Card>

      <Card>
        {loading ? (
          <SkeletonRows rows={8} />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No companies found">
            The registry is seeded from the NSE list on first boot.
          </EmptyState>
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.items}
              rowKey={(c) => c.id}
              onRowClick={(c) => router.push(`/companies/${c.id}`)}
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
