"use client";

/**
 * Client shell that gates the app chrome behind authentication.
 *
 * - While the session is being restored, shows a neutral loading screen.
 * - When no user is authenticated, shows the login form (no sidebar/topbar).
 * - Once authenticated, renders the full Sidebar + Topbar + page layout.
 *
 * This is client-side protection (the API enforces auth server-side regardless);
 * it keeps unauthenticated users out of the data UI without a round-trip redirect.
 */
import { useAuth } from "@/lib/auth";
import { LoginForm } from "@/components/auth/LoginForm";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { Loading } from "@/components/ui/states";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loading label="Restoring session" />
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1600px] px-6 py-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
