import type { Job, UploadResponse } from "./types";

// Dev me Vite proxy "/api" -> localhost:8000 forward karta hai (vite.config.ts
// dekho) - CORS ka jhanjhat nahi. Production build me VITE_API_BASE_URL env
// var se real backend URL set hoga (Phase 11, deployment ke time).
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function uploadInvoices(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function listJobs(): Promise<Job[]> {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) throw new Error(`Could not load jobs (${res.status})`);
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Could not load job (${res.status})`);
  return res.json();
}

export function sampleDataUrl(): string {
  return `${API_BASE}/sample-data`;
}

// Deletes a job row (and its stored file, best-effort, on the backend side) -
// mainly for clearing out failed/test uploads from the list.
export async function deleteJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Could not delete job (${res.status})`);
}

// One human-in-the-loop comment on one low-confidence field - "sent" flags it
// onward to the review team, "resolved" means a person signed off on it.
// Returns the updated job (with the new review_notes) so the caller can patch
// local state without a full refetch.
export async function submitReview(
  jobId: string,
  fieldKey: string,
  comment: string,
  action: "sent" | "resolved",
): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ field_key: fieldKey, comment, action }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Could not submit review (${res.status})`);
  }
  return res.json();
}

// Websocket URL API_BASE se derive karta hai (http -> ws, https -> wss)
// taaki dev proxy aur production dono me sahi se kaam kare.
export function jobsWebSocketUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    const base = new URL(import.meta.env.VITE_API_BASE_URL, window.location.href);
    const proto = base.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${base.host}/ws/jobs`;
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/jobs`;
}
