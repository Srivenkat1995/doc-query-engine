"use client";

import { ChangeEvent, FormEvent, useState } from "react";

import {
  createProcessingJob,
  dispatchProcessingJob,
  getProcessingStatus,
  MAX_UPLOAD_BYTES,
  SUPPORTED_UPLOAD_TYPES,
  uploadInvoice,
  type InvoiceResponse,
} from "../lib/api";

const MAX_STATUS_POLLS = 30;
const STATUS_POLL_INTERVAL_MS = 2000;

const formatBytes = (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(2)} MB`;

export function UploadForm() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [uploadedInvoice, setUploadedInvoice] = useState<InvoiceResponse | null>(
    null,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [processingMessage, setProcessingMessage] = useState<string | null>(null);

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadedInvoice(null);
    setRequestError(null);
    setProcessingMessage(null);

    if (!file) {
      setValidationError(null);
    } else if (!SUPPORTED_UPLOAD_TYPES.includes(file.type)) {
      setValidationError("Choose a PDF, JPEG, or PNG invoice.");
    } else if (file.size > MAX_UPLOAD_BYTES) {
      setValidationError("The invoice must be no larger than 5MB.");
    } else {
      setValidationError(null);
    }
  };

  const submitUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile || validationError) return;

    setIsSubmitting(true);
    setRequestError(null);
    setUploadedInvoice(null);
    try {
      const invoice = await uploadInvoice(selectedFile);
      setUploadedInvoice(invoice);
      setSelectedFile(null);
      event.currentTarget.reset();
      setProcessingMessage("Upload complete. Preparing processing…");
      const job = await createProcessingJob(invoice.id, `upload-${invoice.id}`);
      await dispatchProcessingJob(invoice.id, job.id);

      for (let poll = 0; poll < MAX_STATUS_POLLS; poll += 1) {
        const processing = await getProcessingStatus(invoice.id, job.id);
        if (processing.job_status === "completed") {
          setProcessingMessage("Processing complete. Your invoice is ready to review.");
          return;
        }
        if (processing.job_status === "failed" || processing.invoice_status === "failed") {
          throw new Error(
            processing.failure_reason ?? "Processing failed. You can retry this invoice.",
          );
        }
        if (processing.invoice_status === "needs_review") {
          setProcessingMessage("Processing complete. This invoice needs your review.");
          return;
        }
        setProcessingMessage(
          processing.job_status === "queued"
            ? "Queued for processing…"
            : "Processing invoice…",
        );
        await new Promise((resolve) => setTimeout(resolve, STATUS_POLL_INTERVAL_MS));
      }
      throw new Error("Processing is taking longer than expected. You can retry shortly.");
    } catch (error: unknown) {
      setRequestError(
        error instanceof Error ? error.message : "The invoice could not be uploaded.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
          Start a review
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">
          Upload an invoice
        </h2>
        <p className="mt-2 text-slate-600">
          Files are checked before they leave your browser. Maximum size: 5MB.
        </p>
      </div>

      <form className="mt-6" onSubmit={submitUpload}>
        <label
          className="flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-10 text-center transition hover:border-blue-500 hover:bg-blue-50/40"
          htmlFor="invoice-file"
        >
          <span className="font-medium text-slate-900">
            {selectedFile ? selectedFile.name : "Choose an invoice file"}
          </span>
          <span className="mt-2 text-sm text-slate-500">
            PDF, JPEG, or PNG
            {selectedFile && ` · ${formatBytes(selectedFile.size)}`}
          </span>
          <input
            accept={SUPPORTED_UPLOAD_TYPES.join(",")}
            className="sr-only"
            id="invoice-file"
            onChange={selectFile}
            type="file"
          />
        </label>

        {validationError && (
          <p className="mt-3 text-sm text-rose-700" role="alert">
            {validationError}
          </p>
        )}
        {requestError && (
          <p className="mt-3 text-sm text-rose-700" role="alert">
            {requestError}
          </p>
        )}
        {uploadedInvoice && processingMessage && (
          <p className="mt-3 text-sm text-emerald-700" role="status">
            Uploaded {uploadedInvoice.original_filename}. {processingMessage}
          </p>
        )}

        <button
          className="mt-5 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={!selectedFile || Boolean(validationError) || isSubmitting}
          type="submit"
        >
          {isSubmitting ? "Uploading…" : "Upload invoice"}
        </button>
      </form>
    </section>
  );
}
