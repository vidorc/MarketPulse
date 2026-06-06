"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError, api } from "@/lib/api";
import { CsvValidationResponse, ProcessRunResponse } from "@/lib/types";

type Phase = "idle" | "validating" | "validated" | "processing" | "done";

export default function UploadPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [report, setReport] = useState<CsvValidationResponse | null>(null);
  const [result, setResult] = useState<ProcessRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asyncMode, setAsyncMode] = useState(false);

  const reset = () => {
    setPhase("idle");
    setFile(null);
    setReport(null);
    setResult(null);
    setError(null);
  };

  const onValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setPhase("validating");
    setError(null);
    setReport(null);
    try {
      const r = await api.uploadCsv(file);
      setReport(r);
      setPhase("validated");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
      setPhase("idle");
    }
  };

  const onProcess = async () => {
    if (!report?.run_id) return;
    setPhase("processing");
    setError(null);
    try {
      const r = await api.processRun(report.run_id, asyncMode);
      setResult(r);
      setPhase("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Processing failed.");
      setPhase("validated");
    }
  };

  return (
    <div className="mx-auto max-w-3xl [animation:fade-in_0.4s_ease-out_both]">
      <PageHeader
        title="Upload CSV"
        subtitle="Validate a news CSV, preview rows, then run the extraction pipeline."
      />

      {/* Step 1 */}
      <Card className="mb-4">
        <CardHeader title="1 · Select file" />
        <CardBody>
          <form onSubmit={onValidate} className="space-y-3">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setReport(null);
                setResult(null);
                setPhase("idle");
              }}
              className="block w-full text-[12.5px] text-ink-soft file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-gradient-to-b file:from-gold-bright file:to-gold file:px-3.5 file:py-1.5 file:text-[12px] file:font-semibold file:uppercase file:tracking-wide file:text-ground"
            />
            <p className="text-[11px] text-muted">
              Required column: <code className="text-gold">title</code>. Optional:{" "}
              <code>article_text</code>/<code>body</code>, <code>url</code>,{" "}
              <code>source</code>, <code>date_published</code>.
            </p>
            <Button
              type="submit"
              variant="primary"
              disabled={!file || phase === "validating"}
            >
              {phase === "validating" ? "Validating…" : "Validate"}
            </Button>
          </form>
        </CardBody>
      </Card>

      {error && (
        <Card className="mb-4 border-neg/30">
          <CardBody>
            <p className="text-[12.5px] text-neg">{error}</p>
          </CardBody>
        </Card>
      )}

      {/* Step 2 */}
      {report && (
        <Card className="mb-4">
          <CardHeader
            title="2 · Validation report"
            action={
              <Badge
                kind="status"
                value={report.valid ? "processed" : "failed"}
                label={report.valid ? "valid" : "issues found"}
              />
            }
          />
          <CardBody className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <Metric label="Total rows" value={report.total_rows} />
              <Metric label="Valid rows" value={report.valid_rows} />
              <Metric label="Columns" value={report.columns.length} />
            </div>

            {report.issues.length > 0 && (
              <div className="rounded-md border border-medium/30 bg-medium/[0.06] p-2.5">
                <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-medium">
                  Issues
                </div>
                <ul className="list-inside list-disc text-[12.5px] text-ink-soft">
                  {report.issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.preview.length > 0 && <PreviewTable rows={report.preview} />}

            {report.valid && report.run_id != null ? (
              <div className="flex items-center gap-3 border-t border-line pt-3">
                <label className="flex items-center gap-2 text-[11px] uppercase tracking-wide text-muted">
                  <input
                    type="checkbox"
                    checked={asyncMode}
                    onChange={(e) => setAsyncMode(e.target.checked)}
                    className="accent-gold"
                  />
                  Async (Celery)
                </label>
                <Button
                  variant="primary"
                  onClick={onProcess}
                  disabled={phase === "processing"}
                >
                  {phase === "processing"
                    ? "Processing…"
                    : `Process ${report.valid_rows} rows`}
                </Button>
              </div>
            ) : (
              <p className="text-[12.5px] text-muted">
                Fix the issues above and re-upload to enable processing.
              </p>
            )}
          </CardBody>
        </Card>
      )}

      {/* Step 3 */}
      {result && (
        <Card className="border-pos/30">
          <CardHeader title="3 · Run result" />
          <CardBody className="space-y-3">
            <div className="grid grid-cols-4 gap-3">
              <Metric label="Run" value={`#${result.run_id}`} />
              <Metric label="Total" value={result.total_rows} />
              <Metric label="Processed" value={result.processed} />
              <Metric label="Failed" value={result.failed} />
            </div>
            <div className="flex items-center gap-2">
              <Badge kind="status" value={result.status} />
              <span className="text-[12.5px] text-muted">
                {result.status === "queued"
                  ? "Dispatched to the worker. Check the feed shortly."
                  : "Run complete."}
              </span>
            </div>
            <div className="flex gap-2 border-t border-line pt-3">
              <Button variant="primary" onClick={() => router.push("/feed")}>
                View feed
              </Button>
              <Button variant="subtle" onClick={reset}>
                Upload another
              </Button>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-line bg-surface p-2.5">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted">
        {label}
      </div>
      <div className="tnum mt-0.5 text-[19px] font-semibold text-ink">
        {value}
      </div>
    </div>
  );
}

function PreviewTable({ rows }: { rows: Record<string, unknown>[] }) {
  const cols = Array.from(
    rows.reduce((set, r) => {
      Object.keys(r).forEach((k) => set.add(k));
      return set;
    }, new Set<string>())
  ).slice(0, 6);

  return (
    <div className="overflow-x-auto rounded-md border border-line">
      <table className="w-full border-collapse text-[11px]">
        <thead>
          <tr className="border-b border-line bg-panel-2">
            {cols.map((c) => (
              <th
                key={c}
                className="px-2.5 py-1.5 text-left font-medium uppercase tracking-wide text-muted"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 5).map((r, i) => (
            <tr key={i} className="border-b border-line/40">
              {cols.map((c) => (
                <td
                  key={c}
                  className="max-w-[240px] truncate px-2.5 py-1.5 text-ink-soft"
                >
                  {String(r[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
