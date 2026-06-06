"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import clsx from "@/lib/clsx";

type Health = "checking" | "online" | "offline";

const TITLES: Record<string, string> = {
  "": "Dashboard",
  feed: "News Feed",
  companies: "Company Explorer",
  upload: "Upload CSV",
  articles: "Article Review",
  benchmarks: "Benchmarks",
  performance: "Model Performance",
  audit: "Audit Logs",
  settings: "Settings",
};

/** Polls /health so an analyst can see at a glance whether the API is reachable. */
export function Topbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<Health>("checking");

  useEffect(() => {
    let cancelled = false;
    const check = () => {
      api
        .health()
        .then(() => !cancelled && setHealth("online"))
        .catch(() => !cancelled && setHealth("offline"));
    };
    check();
    const id = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const segment = pathname.split("/")[1] ?? "";
  const crumb = TITLES[segment] ?? "Dashboard";

  const dot =
    health === "online"
      ? "bg-pos"
      : health === "offline"
        ? "bg-neg"
        : "bg-medium";

  const label =
    health === "online"
      ? "API Online"
      : health === "offline"
        ? "API Offline"
        : "Checking";

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-line bg-surface/60 px-6 backdrop-blur lg:px-8">
      <div className="flex items-center gap-2 text-[12px]">
        <span className="text-faint">MarketPulse</span>
        <span className="text-faint">/</span>
        <span className="font-medium text-ink-soft">{crumb}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-1.5 text-[10px] uppercase tracking-[0.12em] text-faint sm:flex">
          <span>NSE Equity News</span>
          <span className="text-line-bright">·</span>
          <span>LLM Pipeline</span>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-line bg-panel px-2.5 py-1">
          <span className="relative flex h-2 w-2">
            {health === "online" && (
              <span className="absolute inline-flex h-full w-full rounded-full bg-pos/60 opacity-75 [animation:pulse-dot_2s_ease-in-out_infinite]" />
            )}
            <span className={clsx("relative inline-flex h-2 w-2 rounded-full", dot)} />
          </span>
          <span className="text-[10.5px] font-medium uppercase tracking-wide text-muted">
            {label}
          </span>
        </div>

        {user && (
          <div className="flex items-center gap-2.5 border-l border-line pl-4">
            <div className="hidden text-right leading-tight sm:block">
              <div className="text-[12px] font-medium text-ink-soft">
                {user.full_name || user.email}
              </div>
              <div className="text-[9.5px] uppercase tracking-[0.14em] text-gold/80">
                {user.role}
              </div>
            </div>
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-gold-bright to-gold text-[12px] font-bold text-ground">
              {(user.full_name || user.email).charAt(0).toUpperCase()}
            </div>
            <button
              onClick={logout}
              title="Sign out"
              className="rounded-md border border-line px-2 py-1 text-[10.5px] font-medium uppercase tracking-wide text-muted transition-colors hover:border-line-bright hover:text-ink"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
