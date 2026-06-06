"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Column, DataTable } from "@/components/ui/DataTable";
import { ErrorState, Loading } from "@/components/ui/states";
import { ApiError, api } from "@/lib/api";
import { formatDate, humanize } from "@/lib/format";
import { ARTICLE_TYPES, CompanyMention } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const INPUT =
  "w-full rounded-md border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

export default function ArticleReviewPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  const { data, loading, error, reload } = useApi(
    () => api.getArticle(id),
    [id]
  );

  return (
    <div>
      <PageHeader
        title="Article Review"
        subtitle="Full LLM extraction with analyst correction."
        action={
          <Link href="/feed">
            <Button variant="subtle">← Back to feed</Button>
          </Link>
        }
      />

      {loading ? (
        <Loading label="Loading article" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data ? null : (
        <div className="grid grid-cols-1 gap-4 [animation:fade-in_0.4s_ease-out_both] lg:grid-cols-3">
          {/* Left: article content */}
          <div className="space-y-4 lg:col-span-2">
            <Card>
              <CardHeader title="Article" />
              <CardBody className="space-y-3">
                <h2 className="text-[17px] font-semibold leading-snug text-ink">
                  {data.title}
                </h2>
                <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted">
                  {data.source && <span>{data.source}</span>}
                  <span className="text-line-bright">·</span>
                  <span className="tnum">{formatDate(data.created_at)}</span>
                  <Badge kind="status" value={data.status} />
                  {data.url && (
                    <a
                      href={data.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-gold underline-offset-2 hover:underline"
                    >
                      source ↗
                    </a>
                  )}
                </div>
                <p className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-ink-soft">
                  {data.body}
                </p>
              </CardBody>
            </Card>

            <Card>
              <CardHeader title="Extracted companies" />
              <CompaniesTable companies={data.companies} />
            </Card>
          </div>

          {/* Right: classification + correction */}
          <div className="space-y-4">
            <Card>
              <CardHeader title="Classification" />
              <CardBody className="space-y-3.5">
                {data.classification ? (
                  <>
                    <Field label="Article type">
                      <Badge
                        kind="type"
                        value={humanize(data.classification.article_type)}
                      />
                    </Field>
                    <Field label="Impact">
                      <Badge kind="impact" value={data.classification.impact} />
                    </Field>
                    <Field label="Confidence">
                      <span className="tnum font-semibold text-ink">
                        {data.classification.confidence}
                        <span className="text-muted">/100</span>
                      </span>
                    </Field>
                    <div>
                      <div className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
                        Reasoning
                      </div>
                      <p className="rounded-md border border-line bg-surface p-2.5 text-[12.5px] leading-relaxed text-ink-soft">
                        {data.classification.reasoning || "—"}
                      </p>
                    </div>
                  </>
                ) : (
                  <p className="text-[12.5px] text-muted">
                    Not classified (article still pending).
                  </p>
                )}
              </CardBody>
            </Card>

            <CorrectionForm
              articleId={id}
              currentTickers={data.companies
                .map((c) => c.ticker)
                .filter((t): t is string => Boolean(t))}
              currentType={data.classification?.article_type ?? null}
              onSaved={reload}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
        {label}
      </span>
      {children}
    </div>
  );
}

function CompaniesTable({ companies }: { companies: CompanyMention[] }) {
  const columns: Column<CompanyMention>[] = [
    {
      key: "company",
      header: "Company",
      render: (c) => (
        <Link
          href={`/companies/${c.company_id}`}
          className="font-medium text-ink hover:text-gold"
        >
          {c.company_name}
        </Link>
      ),
    },
    {
      key: "ticker",
      header: "Ticker",
      render: (c) =>
        c.ticker ? (
          <Badge value={c.ticker} />
        ) : (
          <span className="text-faint">unmapped</span>
        ),
    },
    {
      key: "sentiment",
      header: "Sentiment",
      align: "center",
      render: (c) =>
        c.sentiment ? (
          <Badge kind="sentiment" value={c.sentiment} />
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    {
      key: "alias",
      header: "Alias used",
      render: (c) => <span className="text-muted">{c.alias_used ?? "—"}</span>,
    },
    {
      key: "conf",
      header: "Conf",
      align: "right",
      render: (c) => <span className="tnum text-ink-soft">{c.confidence}</span>,
    },
    {
      key: "flag",
      header: "",
      render: (c) =>
        c.is_manual_correction ? <Badge kind="type" value="manual" /> : null,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={companies}
      rowKey={(c) => c.company_id}
      emptyLabel="No companies extracted (broad/technical article)."
    />
  );
}

function CorrectionForm({
  articleId,
  currentTickers,
  currentType,
  onSaved,
}: {
  articleId: number;
  currentTickers: string[];
  currentType: string | null;
  onSaved: () => void;
}) {
  const [tickers, setTickers] = useState(currentTickers.join(", "));
  const [type, setType] = useState(currentType ?? "");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(
    null
  );

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    const parsed = tickers
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);
    try {
      await api.correctArticle(articleId, {
        tickers: parsed,
        article_type: type || null,
      });
      setMsg({ kind: "ok", text: "Correction saved and audited." });
      onSaved();
    } catch (err) {
      setMsg({
        kind: "err",
        text:
          err instanceof ApiError ? err.message : "Failed to save correction.",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader title="Analyst correction" />
      <CardBody>
        <form onSubmit={submit} className="space-y-3.5">
          <div>
            <label className="mb-1.5 block text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
              Tickers (comma-separated)
            </label>
            <input
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              placeholder="RELIANCE, TCS"
              className={`${INPUT} uppercase`}
            />
            <p className="mt-1.5 text-[10.5px] text-muted">
              Replaces the article&apos;s company links. Unknown tickers are
              ignored.
            </p>
          </div>
          <div>
            <label className="mb-1.5 block text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
              Article type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className={INPUT}
            >
              <option value="">Leave unchanged</option>
              {ARTICLE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {humanize(t)}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? "Saving…" : "Save correction"}
          </Button>
          {msg && (
            <p
              className={
                msg.kind === "ok"
                  ? "text-[11px] text-pos"
                  : "text-[11px] text-neg"
              }
            >
              {msg.text}
            </p>
          )}
        </form>
      </CardBody>
    </Card>
  );
}
