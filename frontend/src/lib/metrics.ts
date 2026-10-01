// Single source of truth for every number the landing page shows. Every
// value here is copied character-for-character from results-log.md (the
// project's measured-results log) - nothing on this page is invented or
// rounded for effect. If a number here ever needs to change, it should be
// because results-log.md changed, never the other way round.

export const ACCURACY_PROGRESSION = [
  { label: "OCR + regex rules", sub: "Baseline A", value: 2.0 },
  { label: "Pretrained, zero-shot", sub: "Baseline B (different checkpoint)", value: 42.6 },
  { label: "Fine-tuned LoRA (CORD only)", sub: "Our own training", value: 86.8 },
  { label: "+ synthetic Indian invoices", sub: "Adds GSTIN/vendor/date/HSN fields", value: 89.5 },
] as const;

export const TRAINING_EFFICIENCY = {
  trainableParams: "932,413",
  totalParams: "126,896,890",
  trainablePct: "0.73%",
  vram: "6GB",
  gpu: "RTX 4050 Laptop",
};

export const CALIBRATION = {
  eceBefore: 1.03,
  eceAfter: 0.96,
  temperature: 0.95,
};

export const STP_TABLE = [
  { threshold: 0.5, stpPct: 94.8, errorPct: 4.5 },
  { threshold: 0.7, stpPct: 91.6, errorPct: 3.51 },
  { threshold: 0.9, stpPct: 85.7, errorPct: 2.52 },
  { threshold: 0.95, stpPct: 81.6, errorPct: 2.34 },
  { threshold: 0.99, stpPct: 65.7, errorPct: 1.53 },
] as const;

export const STP_HEADLINE = {
  threshold: 90,
  autoApprovePct: 85.7,
  errorPct: 2.52,
};

export const LATENCY = [
  { backend: "PyTorch fp32 — GPU (RTX 4050)", ms: 50.2, sizeMb: 507.5, exact: 91.46 },
  { backend: "PyTorch fp32 — CPU", ms: 1651.0, sizeMb: 507.5, exact: 91.46 },
  { backend: "ONNX fp32 — CPU", ms: 1993.5, sizeMb: 505.8, exact: 91.46 },
  { backend: "ONNX INT8 — CPU", ms: 1405.2, sizeMb: 128.5, exact: 87.94 },
] as const;

export const GPU_VS_CPU_SPEEDUP = "33x";
export const QUANTIZATION_SHRINK = "4x";
export const QUANTIZATION_ACCURACY_COST = 3.52;

export const NEW_FIELD_TYPES = [
  "Vendor name",
  "GSTIN",
  "Invoice number",
  "Invoice date",
  "HSN code",
  "CGST amount",
  "SGST amount",
];

// Real OCR failure strings, taken verbatim from the Baseline A diagnostic in
// results-log.md - genuine garbage output from Tesseract on hard receipts,
// not fabricated "messy data" examples.
export const REAL_OCR_GARBAGE = ["'= eGan'", "'rT a'", "'11 lI l'", "'0Ca5h'"];

export const PIPELINE_STAGES = [
  {
    n: "01",
    title: "Upload",
    detail: "Single receipt or a whole batch, one endpoint, each gets its own async job.",
  },
  {
    n: "02",
    title: "OCR",
    detail: "Tesseract reads raw pixels into words + bounding boxes for anything without ground truth.",
  },
  {
    n: "03",
    title: "LayoutLMv3 + LoRA",
    detail: "A 133M-parameter layout-aware transformer classifies every token — only 0.73% of it was actually trained.",
  },
  {
    n: "04",
    title: "Field grouping",
    detail: "Token-level BIO tags get grouped into the 13 fields a business actually needs.",
  },
  {
    n: "05",
    title: "Calibration",
    detail: "Temperature scaling turns raw softmax scores into a number you can actually trust as a probability.",
  },
  {
    n: "06",
    title: "STP decision",
    detail: "Above the threshold, a field auto-approves. Below it, a human reviews — the system knows what it doesn't know.",
  },
] as const;

// Phase 14: the live per-document progress cards (ProcessingOverlay.tsx)
// show the backend's REAL ephemeral sub-stage keys - see
// src/api/status_bus.py's publish_status docstring and src/api/tasks.py's
// _on_stage callback. These are coarser than the 6 marketing steps above
// (there's no real mid-pipeline "Upload" or "STP decision" event to hook
// into), so this is a separate, smaller mapping, wording reused from
// PIPELINE_STAGES above where it overlaps rather than invented fresh.
export const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  ocr: "Reading text (OCR)",
  model: "Running LayoutLMv3 + LoRA",
  decoding: "Grouping fields + confidence",
  done: "Done",
  failed: "Failed",
};

// Order the live progress-bar segments render in (excludes "failed", which
// gets its own card treatment instead of a position on the bar).
export const STAGE_ORDER = ["queued", "ocr", "model", "decoding", "done"] as const;
