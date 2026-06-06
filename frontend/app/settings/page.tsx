"use client";

import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Column, DataTable } from "@/components/ui/DataTable";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useApi } from "@/lib/useApi";
import type { UserOut, UserRole } from "@/lib/types";

const INPUT =
  "rounded-md border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

const ROLES: UserRole[] = ["viewer", "analyst", "admin"];

function UserManagement() {
  const { data, loading, error, reload } = useApi(() => api.listUsers(), []);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("analyst");
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setBusy(true);
    try {
      await api.createUser({ email, password, role });
      setEmail("");
      setPassword("");
      setRole("analyst");
      reload();
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : "Failed to create user."
      );
    } finally {
      setBusy(false);
    }
  };

  const columns: Column<UserOut>[] = [
    {
      key: "email",
      header: "Email",
      render: (u) => <span className="font-medium text-ink">{u.email}</span>,
    },
    {
      key: "name",
      header: "Name",
      render: (u) => u.full_name || <span className="text-faint">—</span>,
    },
    {
      key: "role",
      header: "Role",
      render: (u) => (
        <span className="rounded-sm border border-gold/25 bg-gold/[0.06] px-1.5 py-0.5 text-[10.5px] font-medium uppercase tracking-wider text-gold">
          {u.role}
        </span>
      ),
    },
    {
      key: "active",
      header: "Status",
      align: "center",
      render: (u) => (
        <span className={u.is_active ? "text-pos" : "text-neg"}>
          {u.is_active ? "Active" : "Disabled"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title="Create user" />
        <CardBody>
          <form onSubmit={create} className="flex flex-wrap items-center gap-2">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@company.com"
              className={`min-w-[220px] flex-1 ${INPUT}`}
            />
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (min 8)"
              className={INPUT}
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className={INPUT}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
            <Button type="submit" variant="primary" disabled={busy}>
              {busy ? "Creating…" : "Create"}
            </Button>
          </form>
          {formError && (
            <p className="mt-2 text-[12px] text-neg">{formError}</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Users"
          action={
            data && (
              <span className="text-[11px] text-muted">{data.total} total</span>
            )
          }
        />
        {loading ? (
          <SkeletonRows rows={4} />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No users" />
        ) : (
          <DataTable columns={columns} rows={data.items} rowKey={(u) => u.id} />
        )}
      </Card>
    </div>
  );
}

function RuntimeConfig() {
  // Honest, non-secret runtime facts the browser actually knows.
  const rows: [string, string][] = [
    ["API base URL", api.baseUrl],
    ["Environment", process.env.NODE_ENV ?? "unknown"],
  ];
  return (
    <Card>
      <CardHeader title="Runtime configuration" />
      <CardBody>
        <dl className="divide-y divide-line">
          {rows.map(([k, v]) => (
            <div key={k} className="flex items-center justify-between py-2">
              <dt className="text-[12px] uppercase tracking-[0.12em] text-muted">
                {k}
              </dt>
              <dd className="tnum text-[12.5px] text-ink-soft">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-[11.5px] text-faint">
          LLM provider and secrets are configured server-side via environment
          variables and are intentionally not exposed to the browser.
        </p>
      </CardBody>
    </Card>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Account, user management, and runtime configuration."
      />
      <div className="space-y-4">
        {isAdmin ? (
          <UserManagement />
        ) : (
          <Card>
            <CardBody>
              <p className="text-[13px] text-muted">
                User management is available to administrators. You are signed in
                as{" "}
                <span className="font-medium text-ink-soft">{user?.email}</span>{" "}
                ({user?.role}).
              </p>
            </CardBody>
          </Card>
        )}
        <RuntimeConfig />
      </div>
    </div>
  );
}
