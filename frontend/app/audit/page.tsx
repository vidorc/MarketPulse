"use client";

import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { api } from "@/lib/api";
import { formatDate, humanize } from "@/lib/format";
import type { AuditLogOut } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const PAGE = 25;

const INPUT =
  "rounded-md border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

/** Compact JSON renderer for before/after payloads. */
function JsonBlock({
  label,
  data,
}: {
  label: string;
  data: Record<string, unknown> | null;
}) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="min-w-0 flex-1">
      <div className="mb-1 text-[9.5px] uppercase tracking-wider text-faint">
        {label}
      </div>
      <pre className="overflow-x-auto rounded-md border border-line bg-surface px-2.5 py-2 font-mono text-[11px] leading-relaxed text-ink-soft">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

function AuditRow({ entry }: { entry: AuditLogOut }) {
  const hasDiff =
    (entry.before && Object.keys(entry.before).length > 0) ||
    (entry.after && Object.keys(entry.after).length > 0);

  return (
    <div className="border-b border-line px-4 py-3 last:border-b-0">
      <div className="flex flex-wrap items-center gap-2">
        <Badge kind="type" value={entry.action} />
        <span className="text-[12px] text-ink-soft">
          {humanize(entry.entity_type)}
          {entry.entity_id != null && (
            <span className="text-muted"> #{entry.entity_id}</span>
          )}
        </span>
        <span className="ml-auto flex items-center gap-3 text-[11px] text-muted">
          <span>
            {entry.actor_id != null ? (
              <>actor #{entry.actor_id}</>
            ) : (
              <span className="text-faint">system</span>
            )}
          </span>
          <span className="tnum">{formatDate(entry.created_at)}</span>
        </span>
      </div>

      {entry.message && (
        <p className="mt-1.5 text-[12px] text-muted">{entry.message}</p>
      )}

      {hasDiff && (
        <div className="mt-2.5 flex flex-col gap-2.5 sm:flex-row">
          <JsonBlock label="Before" data={entry.before} />
          <JsonBlock label="After" data={entry.after} />
        </div>
      )}
    </div>
  );
}

export default function AuditPage() {
  const [offset, setOffset] = useState(0);
  const [entityType, setEntityType] = useState("");
  const [action, setAction] = useState("");

  const { data, loading, error, reload } = useApi(
    () =>
      api.listAudit({
        limit: PAGE,
        offset,
        entity_type: entityType || undefined,
        action: action || undefined,
      }),
    [offset, entityType, action]
  );

  return (
    <div>
      <PageHeader
        title="Audit Logs"
        subtitle="System pipeline events and analyst actions, with before / after diffs."
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-2 p-2.5">
          <select
            value={entityType}
            onChange={(e) => {
              setOffset(0);
              setEntityType(e.target.value);
            }}
            className={INPUT}
          >
            <option value="">All entities</option>
            <option value="article">Article</option>
            <option value="benchmark">Benchmark</option>
            <option value="ground_truth">Ground truth</option>
            <option value="user">User</option>
          </select>
          <input
            value={action}
            onChange={(e) => {
              setOffset(0);
              setAction(e.target.value);
            }}
            placeholder="Filter by action (e.g. article_corrected)"
            className={`min-w-[260px] flex-1 ${INPUT}`}
          />
        </div>
      </Card>

      <Card>
        {loading ? (
          <SkeletonRows rows={8} />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No audit entries">
            Pipeline runs and analyst corrections are recorded here as they
            happen.
          </EmptyState>
        ) : (
          <>
            <div>
              {data.items.map((e) => (
                <AuditRow key={e.id} entry={e} />
              ))}
            </div>
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
