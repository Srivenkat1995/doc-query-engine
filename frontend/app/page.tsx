"use client";

import { useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "../lib/api";
import { UploadForm } from "../components/upload-form";
import { InvoiceDashboard } from "../components/invoice-dashboard";

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((requestError: unknown) => {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to connect to the backend",
      );
    });
  }, []);

  return (
    <main className="min-h-screen px-6 py-16 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <header className="mb-14 max-w-2xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
            Document Query Engine
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-6xl">
            Find invoice exceptions before they become payment mistakes.
          </h1>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Upload, query, and verify extracted invoice data against its source
            document.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-950">
                Backend connection
              </h2>
              <p className="mt-2 text-slate-600">
                The frontend checks the API before the invoice workflow begins.
              </p>
            </div>
            <div
              className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-sm font-medium ${
                health
                  ? "bg-emerald-100 text-emerald-800"
                  : error
                    ? "bg-rose-100 text-rose-800"
                    : "bg-slate-100 text-slate-600"
              }`}
            >
              {health ? "Connected" : error ? "Unavailable" : "Checking…"}
            </div>
          </div>

          {health && (
            <dl className="mt-8 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-3">
              <div>
                <dt className="text-sm text-slate-500">Service</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {health.service}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Version</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {health.version}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Environment</dt>
                <dd className="mt-1 font-medium capitalize text-slate-900">
                  {health.environment}
                </dd>
              </div>
            </dl>
          )}

          {error && (
            <div className="mt-8 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
              {error}. Start the FastAPI service and refresh this page.
            </div>
          )}
        </section>

        <div className="mt-8">
          <UploadForm />
        </div>
        <InvoiceDashboard />
      </div>
    </main>
  );
}
