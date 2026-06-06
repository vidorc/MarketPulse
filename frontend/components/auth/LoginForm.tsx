"use client";

/**
 * Login / sign-up form shown when no user is authenticated. Defaults to login;
 * a toggle switches to self-registration (which always creates a viewer account,
 * then logs straight in).
 */
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const INPUT =
  "w-full rounded-md border border-line bg-surface px-3 py-2 text-[13px] text-ink-soft outline-none transition-colors placeholder:text-faint focus:border-gold/50 focus:ring-2 focus:ring-gold/15";

export function LoginForm() {
  const { login } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register({
          email,
          password,
          full_name: fullName || null,
        });
      }
      await login(email, password);
      // On success the AppShell re-renders into the authenticated layout.
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again."
      );
      setBusy(false);
    }
  };

  return (
    <div className="app-bg flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-gold-bright to-gold shadow-glow">
            <span className="text-[16px] font-bold text-ground">M</span>
          </div>
          <div className="leading-tight">
            <div className="text-[16px] font-semibold tracking-tight text-ink">
              MarketPulse
            </div>
            <div className="text-[9.5px] uppercase tracking-[0.16em] text-muted">
              Market Intelligence
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-line bg-panel p-6 shadow-panel">
          <h1 className="mb-1 text-[15px] font-semibold text-ink">
            {mode === "login" ? "Sign in" : "Create your account"}
          </h1>
          <p className="mb-5 text-[12px] text-muted">
            {mode === "login"
              ? "Access the market intelligence workspace."
              : "New accounts start with viewer access."}
          </p>

          <form onSubmit={submit} className="space-y-3">
            {mode === "register" && (
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Full name (optional)"
                className={INPUT}
                autoComplete="name"
              />
            )}
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className={INPUT}
              autoComplete="email"
            />
            <input
              type="password"
              required
              minLength={mode === "register" ? 8 : 1}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className={INPUT}
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
            />

            {error && (
              <div className="rounded-md border border-neg/30 bg-neg/[0.06] px-3 py-2 text-[12px] text-neg">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              disabled={busy}
              className="w-full py-2"
            >
              {busy
                ? "Please wait…"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </Button>
          </form>

          <div className="mt-4 text-center text-[12px] text-muted">
            {mode === "login" ? (
              <>
                No account?{" "}
                <button
                  onClick={() => {
                    setMode("register");
                    setError(null);
                  }}
                  className="text-gold hover:underline"
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  onClick={() => {
                    setMode("login");
                    setError(null);
                  }}
                  className="text-gold hover:underline"
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
