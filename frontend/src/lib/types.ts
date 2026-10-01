// Backend (src/api/schemas.py, src/api/models.py) ke saath exactly match
// karta hai - JobStatus enum values wahi hain jo Python JobStatus.*.value
// deta hai.

export type JobStatus = "queued" | "processing" | "done" | "failed";

// Phase 14: an ephemeral, UI-only sub-step inside status === "processing" -
// never persisted to the DB (src/api/status_bus.py's publish_status is the
// source: `stage` only ever travels over the websocket pub/sub message, the
// Job.status column on the backend stays queued/processing/done/failed).
// Drives the live per-document progress cards - see ProcessingOverlay.tsx.
export type JobStage = "queued" | "ocr" | "model" | "decoding" | "done" | "failed";

export interface FieldResult {
  value: string;
  confidence: number;
}

export interface InvoiceResult {
  fields: Record<string, FieldResult>;
  backend: string;
}

// One human-in-the-loop comment on one low-confidence field. "sent" = flagged
// onward to the review team, "resolved" = a person has signed off on it.
export interface ReviewNote {
  comment: string;
  status: "sent" | "resolved";
  updated_at: string;
}

export interface Job {
  id: string;
  filename: string;
  status: JobStatus;
  result: InvoiceResult | null;
  error: string | null;
  review_notes: Record<string, ReviewNote> | null;
  created_at: string;
  updated_at: string;
  // Phase 14, websocket-only: the live sub-step while status is
  // "processing". Absent/null everywhere else (fresh GET /jobs rows,
  // terminal states before any stage push arrived, etc).
  stage?: JobStage | null;
}

export interface UploadResponse {
  jobs: Job[];
}

// Phase 6 (results-log.md "Calibration / STP analysis") ka 90% threshold -
// isi ko UI me bhi review-vs-auto-approve line ke liye use karte hain, taaki
// demo ka number backend ke measured result se match kare, banaya hua na ho.
export const STP_CONFIDENCE_THRESHOLD = 0.9;
