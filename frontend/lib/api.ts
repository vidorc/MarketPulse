/**
 * Thin fetch wrapper around the MarketPulse REST API.
 *
 * All calls are browser-side, so NEXT_PUBLIC_API_BASE_URL must be reachable from
 * the user's browser (localhost:8000 in the default compose setup). Errors are
 * normalized into ApiError so callers and the useApi hook can render a consistent
 * message instead of a raw fetch rejection.
 */
import type {
  AnalyticsOverview,
  ArticleDetail,
  ArticleListResponse,
  AuditListResponse,
  BenchmarkResponse,
  BenchmarkTrendPoint,
  CompanyDetail,
  CompanyListResponse,
  CorrectionRequest,
  CsvValidationResponse,
  GroundTruthCreate,
  GroundTruthListResponse,
  GroundTruthOut,
  LoginRequest,
  ProcessRunResponse,
  RegisterRequest,
  RunBenchmarkResponse,
  Token,
  UserListResponse,
  UserOut,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

const API = `${BASE_URL}/api/v1`;

const TOKEN_STORAGE_KEY = "marketpulse_token";

// In-memory copy of the bearer token, hydrated from localStorage on load so a
// page refresh keeps the session. SSR-safe: guards every window access.
let authToken: string | null = null;

export function getToken(): string | null {
  if (authToken !== null) return authToken;
  if (typeof window === "undefined") return null;
  authToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  return authToken;
}

export function setToken(token: string | null): void {
  authToken = token;
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body && !(init.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the API at ${BASE_URL}. Is the backend running?`
    );
  }

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* keep status-line detail */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// `type` (not `interface`) so these satisfy qs()'s Record index signature.
export type ArticleListParams = {
  limit?: number;
  offset?: number;
  article_type?: string;
  status?: string;
  search?: string;
};

export type CompanyListParams = {
  limit?: number;
  offset?: number;
  search?: string;
};

export const api = {
  baseUrl: BASE_URL,

  health: () => request<{ status: string }>("/health"),

  // Auth
  login: async (payload: LoginRequest) => {
    const tok = await request<Token>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setToken(tok.access_token);
    return tok;
  },
  register: (payload: RegisterRequest) =>
    request<UserOut>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: () => request<UserOut>("/auth/me"),
  logout: () => setToken(null),
  listUsers: () => request<UserListResponse>("/auth/users"),
  createUser: (payload: RegisterRequest) =>
    request<UserOut>("/auth/users", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Articles
  listArticles: (p: ArticleListParams = {}) =>
    request<ArticleListResponse>(`/articles${qs(p)}`),
  getArticle: (id: number) => request<ArticleDetail>(`/articles/${id}`),
  correctArticle: (id: number, payload: CorrectionRequest) =>
    request<ArticleDetail>(`/articles/${id}/corrections`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Ingestion
  uploadCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<CsvValidationResponse>("/articles/upload", {
      method: "POST",
      body: fd,
    });
  },
  processRun: (run_id: number, async_mode = false) =>
    request<ProcessRunResponse>("/articles/process", {
      method: "POST",
      body: JSON.stringify({ run_id, async_mode }),
    }),

  // Companies
  listCompanies: (p: CompanyListParams = {}) =>
    request<CompanyListResponse>(`/companies${qs(p)}`),
  getCompany: (id: number) => request<CompanyDetail>(`/companies/${id}`),

  // Benchmarks & ground truth
  getBenchmarks: () => request<BenchmarkResponse>("/benchmarks"),
  runBenchmark: (run_id?: number) =>
    request<RunBenchmarkResponse>(
      `/benchmarks/run${run_id != null ? `?processing_run_id=${run_id}` : ""}`,
      { method: "POST" }
    ),
  benchmarkTrend: () =>
    request<BenchmarkTrendPoint[]>("/benchmarks/trend"),
  listGroundTruth: () =>
    request<GroundTruthListResponse>("/ground-truth"),
  createGroundTruth: (payload: GroundTruthCreate) =>
    request<GroundTruthOut>("/ground-truth", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Analytics & audit
  getAnalytics: () => request<AnalyticsOverview>("/analytics"),
  listAudit: (p: { limit?: number; offset?: number; entity_type?: string; action?: string } = {}) =>
    request<AuditListResponse>(`/audit${qs(p)}`),
};
