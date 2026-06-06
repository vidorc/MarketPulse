import { Button } from "./Button";

/** Offset/limit pager shared by the feed and company list. */
export function Pagination({
  total,
  limit,
  offset,
  onChange,
}: {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
}) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  const canPrev = offset > 0;
  const canNext = end < total;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="flex items-center justify-between px-4 py-2.5 text-[11px] text-muted">
      <span className="tnum tracking-wide">
        {start}–{end} of {total}
      </span>
      <div className="flex items-center gap-3">
        <span className="tnum tracking-wide">
          page {page} / {pages}
        </span>
        <div className="flex gap-1.5">
          <Button
            variant="subtle"
            disabled={!canPrev}
            onClick={() => onChange(Math.max(0, offset - limit))}
          >
            ← Prev
          </Button>
          <Button
            variant="subtle"
            disabled={!canNext}
            onClick={() => onChange(offset + limit)}
          >
            Next →
          </Button>
        </div>
      </div>
    </div>
  );
}
