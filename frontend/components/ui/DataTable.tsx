import clsx from "@/lib/clsx";
import type { ReactNode } from "react";

/**
 * Minimal table primitives styled for the terminal aesthetic. Generic over the
 * row shape; callers pass column renderers. Sticky header, hover row highlight,
 * and a left accent bar on hover for clickable rows.
 */
export interface Column<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyLabel = "No rows",
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  emptyLabel?: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[12.5px]">
        <thead className="sticky top-0 z-10 bg-panel">
          <tr className="border-b border-line text-left">
            {columns.map((c) => (
              <th
                key={c.key}
                className={clsx(
                  "px-4 py-2.5 text-[10.5px] font-medium uppercase tracking-[0.12em] text-muted",
                  c.align === "right" && "text-right",
                  c.align === "center" && "text-center"
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-10 text-center text-muted"
              >
                {emptyLabel}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={clsx(
                  "border-b border-line/50 transition-colors",
                  onRowClick && "group/row cursor-pointer hover:bg-panel-2"
                )}
              >
                {columns.map((c, ci) => (
                  <td
                    key={c.key}
                    className={clsx(
                      "px-4 py-2.5 align-middle text-ink-soft",
                      ci === 0 &&
                        onRowClick &&
                        "relative before:absolute before:left-0 before:top-1/2 before:h-0 before:-translate-y-1/2 before:rounded-r before:bg-gold before:transition-all before:duration-150 group-hover/row:before:h-[60%] group-hover/row:before:w-[3px]",
                      c.align === "right" && "text-right",
                      c.align === "center" && "text-center",
                      c.className
                    )}
                  >
                    {c.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
