"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "@/lib/clsx";

interface NavItem {
  href: string;
  label: string;
  /** Pages whose backend lands in a later phase are marked so the UI is honest. */
  pending?: boolean;
}

const NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "Intelligence",
    items: [
      { href: "/", label: "Dashboard" },
      { href: "/feed", label: "News Feed" },
      { href: "/companies", label: "Company Explorer" },
      { href: "/upload", label: "Upload CSV" },
    ],
  },
  {
    section: "Quality",
    items: [
      { href: "/benchmarks", label: "Benchmarks" },
      { href: "/performance", label: "Model Performance" },
      { href: "/audit", label: "Audit Logs" },
    ],
  },
  {
    section: "System",
    items: [{ href: "/settings", label: "Settings" }],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-surface/80 backdrop-blur">
      {/* Brand */}
      <div className="flex items-center gap-2.5 border-b border-line px-5 py-4">
        <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-gold-bright to-gold shadow-glow">
          <span className="text-[15px] font-bold text-ground">M</span>
        </div>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-tight text-ink">
            MarketPulse
          </div>
          <div className="text-[9.5px] uppercase tracking-[0.16em] text-muted">
            Market Intelligence
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {NAV.map((group) => (
          <div key={group.section} className="mb-5">
            <div className="px-2 pb-2 text-[9.5px] font-semibold uppercase tracking-[0.16em] text-faint">
              {group.section}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={clsx(
                      "group relative flex items-center justify-between rounded-md px-3 py-2 text-[12.5px] transition-all duration-150",
                      active
                        ? "bg-gold/[0.08] text-gold"
                        : "text-ink-soft hover:bg-panel-2 hover:text-ink"
                    )}
                  >
                    {/* Animated active rail. */}
                    <span
                      className={clsx(
                        "absolute left-0 top-1/2 w-[3px] -translate-y-1/2 rounded-r-full bg-gold transition-all duration-200",
                        active ? "h-5 opacity-100" : "h-0 opacity-0"
                      )}
                    />
                    <span className="font-medium">{item.label}</span>
                    {item.pending && (
                      <span className="rounded-sm border border-line px-1 py-px text-[8.5px] font-medium uppercase tracking-wider text-faint">
                        soon
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="flex items-center justify-between border-t border-line px-5 py-3 text-[10px] uppercase tracking-[0.12em] text-faint">
        <span>v2.0</span>
        <span className="rounded-sm bg-panel-2 px-1.5 py-0.5 text-gold/80">
          Phase 4
        </span>
      </div>
    </aside>
  );
}
