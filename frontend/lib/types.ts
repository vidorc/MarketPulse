/**
 * TypeScript mirrors of the backend Pydantic schemas (backend/app/schemas/*).
 * Kept in sync by hand for now; once auth lands we can generate these from the
 * OpenAPI document the backend already exposes at /openapi.json.
 */

// --- Articles ---

export interface CompanyMention {
  company_id: number;
  company_name: string;
  ticker: string | null;
  alias_used: string | null;
  confidence: number;
  sentiment: string | null;
  is_manual_correction: boolean;
}

export interface ClassificationOut {
  article_type: string;
  impact: string;
  confidence: number;
  reasoning: string;
  raw_llm_json: string;
}

export interface ArticleSummary {
  id: number;
  title: string;
  source: string | null;
  url: string | null;
  status: string;
  article_type: string | null;
  confidence: number | null;
  impact: string | null;
  tickers: string[];
  created_at: string;
}

export interface ArticleDetail {
  id: number;
  title: string;
  body: string;
  source: string | null;
  url: string | null;
  status: string;
  created_at: string;
  classification: ClassificationOut | null;
  companies: CompanyMention[];
}

export interface ArticleListResponse {
  items: ArticleSummary[];
  total: number;
  limit: number;
  offset: number;
}

// --- Ingestion ---

export interface CsvValidationResponse {
  valid: boolean;
  total_rows: number;
  valid_rows: number;
  columns: string[];
  issues: string[];
  preview: Record<string, unknown>[];
  run_id: number | null;
}

export interface ProcessRequest {
  run_id: number;
  async_mode?: boolean;
}

export interface ProcessRunResponse {
  run_id: number;
  status: string;
  total_rows: number;
  processed: number;
  failed: number;
}

export interface CorrectionRequest {
  tickers: string[];
  article_type?: string | null;
}

// --- Companies ---

export interface AliasOut {
  alias_text: string;
  source: string;
}

export interface CompanySummary {
  id: number;
  canonical_name: string;
  ticker: string | null;
  mention_count: number;
}

export interface MentionTimelineEntry {
  article_id: number;
  title: string;
  sentiment: string | null;
  created_at: string;
}

export interface SentimentTrendPoint {
  label: string;
  count: number;
}

export interface CompanyDetail {
  id: number;
  canonical_name: string;
  ticker: string | null;
  aliases: AliasOut[];
  mention_count: number;
  recent_mentions: MentionTimelineEntry[];
  sentiment_trend: SentimentTrendPoint[];
}

export interface CompanyListResponse {
  items: CompanySummary[];
  total: number;
  limit: number;
  offset: number;
}

// --- Shared enums (mirror backend/app/models/enums.py vocabulary) ---

export const ARTICLE_TYPES = [
  "company_specific",
  "market_movers",
  "broker_recommendations",
  "technical_analysis",
  "macro_or_sector",
  "earnings",
  "mergers_and_acquisitions",
  "regulatory",
  "management_commentary",
] as const;

export type Sentiment = "positive" | "neutral" | "negative";
export type Impact = "low" | "medium" | "high";
export type ArticleStatus = "pending" | "processed" | "failed";

// --- Auth & users (mirror backend/app/schemas/auth.py) ---

export type UserRole = "admin" | "analyst" | "viewer";

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string | null;
  role?: UserRole;
}

export interface UserOut {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
}

export interface UserListResponse {
  items: UserOut[];
  total: number;
}

// --- Benchmarks & ground truth (mirror backend/app/schemas/benchmark.py) ---

export interface MetricBlock {
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  tp: number;
  fp: number;
  fn: number;
}

export interface CategoryMetricOut extends MetricBlock {
  category: string;
  rows: number;
}

export interface FalseItemOut {
  title: string;
  predicted: string[];
  expected: string[];
  article_id: number | null;
}

export interface BenchmarkResponse {
  evaluated: number;
  overall: MetricBlock;
  per_category: CategoryMetricOut[];
  false_positives: FalseItemOut[];
  false_negatives: FalseItemOut[];
}

export interface BenchmarkTrendPoint {
  created_at: string;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
}

export interface RunBenchmarkResponse {
  evaluated: number;
  matched_articles: number;
  overall: MetricBlock;
}

export interface GroundTruthOut {
  id: number;
  article_id: number | null;
  title: string;
  expected_tickers: string;
  expected_type: string | null;
  label_source: string;
}

export interface GroundTruthListResponse {
  items: GroundTruthOut[];
  total: number;
}

export interface GroundTruthCreate {
  title: string;
  expected_tickers: string[];
  expected_type?: string | null;
  article_id?: number | null;
}

// --- Analytics & audit (mirror backend/app/schemas/analytics.py) ---

export interface LabelCount {
  label: string;
  count: number;
}

export interface TopCompanyOut {
  company_id: number;
  name: string;
  ticker: string | null;
  mentions: number;
}

export interface AnalyticsOverview {
  total_articles: number;
  processed_articles: number;
  failed_articles: number;
  total_companies: number;
  companies_tagged: number;
  avg_confidence: number;
  total_runs: number;
  article_types: LabelCount[];
  sentiment_distribution: LabelCount[];
  impact_distribution: LabelCount[];
  top_companies: TopCompanyOut[];
  daily_volume: LabelCount[];
  confidence_buckets: LabelCount[];
}

export interface AuditLogOut {
  id: number;
  actor_id: number | null;
  entity_type: string;
  entity_id: string | null;
  action: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  message: string | null;
  created_at: string;
}

export interface AuditListResponse {
  items: AuditLogOut[];
  total: number;
}
