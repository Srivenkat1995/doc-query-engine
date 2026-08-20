"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import {
  getExtraction,
  type ExtractedFieldResponse,
  type ExtractionResponse,
} from "../../../lib/api";

function FieldCard({ field }: { field: ExtractedFieldResponse }) {
  return (
    <article
      className={`rounded-xl border p-4 ${
        field.needs_review
          ? "border-amber-300 bg-amber-50"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-medium capitalize text-slate-900">
          {field.name.replaceAll("_", " ")}
        </h3>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
          {(field.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
      <p className="mt-3 text-lg font-semibold text-slate-950">
        {field.value ?? "No value extracted"}
      </p>
      {field.needs_review && (
        <p className="mt-2 text-sm font-medium text-amber-800">
          Review required: {field.review_reason ?? "uncertain value"}
        </p>
      )}
      {field.citation && (
        <p className="mt-3 border-t border-slate-200 pt-3 text-sm text-slate-600">
          Page {field.citation.page}: “{field.citation.source_text}”
        </p>
      )}
    </article>
  );
}

function ExtractionContent({ extraction }: { extraction: ExtractionResponse }) {
  return (
    <>
      {extraction.issues.length > 0 && (
        <section className="mb-8 rounded-2xl border border-rose-200 bg-rose-50 p-6">
          <h2 className="font-semibold text-rose-950">Review issues</h2>
          <div className="mt-3 space-y-3">
            {extraction.issues.map((issue) => (
              <div key={issue.code} className="text-sm text-rose-800">
                <p className="font-medium">{issue.message}</p>
                <p className="mt-1">
                  Printed total: {issue.details.printed_total ?? "—"} · Calculated:
                  {" "}
                  {issue.details.calculated_total ?? "—"} · Difference:{" "}
                  {issue.details.difference ?? "—"}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="flex items-end justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
              Extracted data
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">
              Verify before acting
            </h2>
          </div>
          <span className="text-sm text-slate-500">
            {extraction.fields.filter((field) => field.needs_review).length} fields need review
          </span>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {extraction.fields.map((field) => (
            <FieldCard field={field} key={field.name} />
          ))}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-950">Line items</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="pb-3 font-medium">Description</th>
                <th className="pb-3 font-medium">Quantity</th>
                <th className="pb-3 font-medium">Unit price</th>
                <th className="pb-3 text-right font-medium">Amount</th>
              </tr>
            </thead>
            <tbody>
              {extraction.line_items.map((item, index) => (
                <tr className="border-b border-slate-100 last:border-0" key={`${item.description}-${index}`}>
                  <td className="py-3 text-slate-900">{item.description}</td>
                  <td className="py-3 text-slate-600">{item.quantity}</td>
                  <td className="py-3 text-slate-600">{item.unit_price}</td>
                  <td className="py-3 text-right font-medium text-slate-900">{item.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <details className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer font-semibold text-slate-950">Source text</summary>
        <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-600">
          {extraction.raw_text}
        </pre>
      </details>
    </>
  );
}

export default function InvoiceReviewPage() {
  const params = useParams<{ invoiceId: string }>();
  const [extraction, setExtraction] = useState<ExtractionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.invoiceId) return;
    getExtraction(params.invoiceId).then(setExtraction).catch((requestError: unknown) => {
      setError(requestError instanceof Error ? requestError.message : "Unable to load invoice extraction.");
    });
  }, [params.invoiceId]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12 sm:px-10">
      <div className="mx-auto max-w-5xl">
        <Link className="text-sm font-medium text-blue-700 hover:text-blue-900" href="/">
          ← Back to upload
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Invoice review
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-slate-950">
            Source-grounded extraction
          </h1>
          <p className="mt-3 text-slate-600">Invoice ID: {params.invoiceId}</p>
        </header>

        {error && (
          <div className="mt-8 rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800" role="alert">
            {error}. The invoice may still be processing.
          </div>
        )}
        {!extraction && !error && (
          <p className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 text-slate-600" role="status">
            Loading extracted data…
          </p>
        )}
        {extraction && <div className="mt-8"><ExtractionContent extraction={extraction} /></div>}
      </div>
    </main>
  );
}
