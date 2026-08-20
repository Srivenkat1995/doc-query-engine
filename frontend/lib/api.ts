export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  environment: string;
};

export type InvoiceResponse = {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  storage_key: string | null;
  status: string;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type JobResponse = {
  id: string;
  invoice_id: string;
  idempotency_key: string;
  status: "queued" | "processing" | "completed" | "failed";
  attempt_count: number;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type ProcessingStatusResponse = {
  invoice_id: string;
  job_id: string;
  invoice_status: "uploaded" | "processing" | "ready" | "needs_review" | "failed";
  job_status: JobResponse["status"];
  attempt_count: number;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;
export const SUPPORTED_UPLOAD_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
];

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Backend health check failed (${response.status})`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function uploadInvoice(file: File): Promise<InvoiceResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${apiBaseUrl}/invoices/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: { message?: string };
    } | null;
    throw new Error(body?.detail?.message ?? "The invoice could not be uploaded.");
  }

  return response.json() as Promise<InvoiceResponse>;
}

async function parseError(response: Response, fallback: string): Promise<Error> {
  const body = (await response.json().catch(() => null)) as {
    detail?: { message?: string };
  } | null;
  return new Error(body?.detail?.message ?? fallback);
}

export async function createProcessingJob(
  invoiceId: string,
  idempotencyKey: string,
): Promise<JobResponse> {
  const response = await fetch(`${apiBaseUrl}/invoices/${invoiceId}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idempotency_key: idempotencyKey }),
  });
  if (!response.ok) throw await parseError(response, "The processing job could not be created.");
  return response.json() as Promise<JobResponse>;
}

export async function dispatchProcessingJob(
  invoiceId: string,
  jobId: string,
): Promise<void> {
  const response = await fetch(
    `${apiBaseUrl}/invoices/${invoiceId}/jobs/${jobId}/dispatch`,
    { method: "POST" },
  );
  if (!response.ok) throw await parseError(response, "The processing job could not be started.");
}

export async function getProcessingStatus(
  invoiceId: string,
  jobId: string,
): Promise<ProcessingStatusResponse> {
  const response = await fetch(
    `${apiBaseUrl}/invoices/${invoiceId}/jobs/${jobId}/status`,
    { cache: "no-store" },
  );
  if (!response.ok) throw await parseError(response, "The processing status could not be read.");
  return response.json() as Promise<ProcessingStatusResponse>;
}
