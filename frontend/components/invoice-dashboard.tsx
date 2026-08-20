"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getDashboard, type DashboardResponse } from "../lib/api";

export function InvoiceDashboard() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [needsReview, setNeedsReview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    getDashboard(needsReview).then(setDashboard).catch((requestError: unknown) => {
      setError(requestError instanceof Error ? requestError.message : "Unable to load invoices.");
    });
  }, [needsReview, reloadKey]);

  return (
    <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Batch overview
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">Exceptions first</h2>
          <p className="mt-2 text-slate-600">Open only what needs your attention.</p>
        </div>
        <button
          className={`rounded-lg px-3 py-2 text-sm font-medium ${needsReview ? "bg-amber-100 text-amber-900" : "bg-slate-100 text-slate-700"}`}
          onClick={() => setNeedsReview((current) => !current)}
          type="button"
        >
          {needsReview ? "Show all invoices" : "Needs review only"}
        </button>
      </div>

      {dashboard && (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <Metric label="Invoices" value={dashboard.total_count} />
          <Metric label="Needs review" value={dashboard.needs_review_count} />
          <Metric label="Failed" value={dashboard.failed_count} />
        </div>
      )}

      {error && (
        <div className="mt-6 flex items-center justify-between gap-4 rounded-xl bg-rose-50 p-4 text-sm text-rose-700" role="alert">
          <span>{error}</span>
          <button
            className="shrink-0 font-semibold underline underline-offset-2"
            onClick={() => {
              setError(null);
              setDashboard(null);
              setReloadKey((key) => key + 1);
            }}
            type="button"
          >
            Retry
          </button>
        </div>
      )}
      {!dashboard && !error && <p className="mt-6 text-sm text-slate-500" role="status">Loading invoice batch…</p>}
      {dashboard?.invoices.length === 0 && (
        <div className="mt-6 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">
          <p className="font-medium text-slate-900">
            {needsReview ? "No invoices need review." : "No invoices uploaded yet."}
          </p>
          <p className="mt-1">
            {needsReview
              ? "That is good news—your exception queue is clear."
              : "Upload an invoice above to start building this batch."}
          </p>
        </div>
      )}
      {dashboard && dashboard.invoices.length > 0 && (
        <div className="mt-6 divide-y divide-slate-100 rounded-xl border border-slate-200">
          {dashboard.invoices.map((invoice) => (
            <Link
              className="flex items-center justify-between gap-4 p-4 transition hover:bg-slate-50"
              href={`/invoices/${invoice.id}`}
              key={invoice.id}
            >
              <div>
                <p className="font-medium text-slate-900">{invoice.original_filename}</p>
                <p className="mt-1 text-sm capitalize text-slate-500">{invoice.status.replaceAll("_", " ")}</p>
              </div>
              <div className="text-right text-sm">
                <p className={invoice.flag_count || invoice.issue_count ? "font-semibold text-amber-800" : "text-slate-600"}>
                  {invoice.flag_count + invoice.issue_count} flags
                </p>
                <p className="mt-1 text-blue-700">Review →</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}
