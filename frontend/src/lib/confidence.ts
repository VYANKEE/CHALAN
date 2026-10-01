import { STP_CONFIDENCE_THRESHOLD } from "./types";

// Phase 6 (results-log.md) ke STP threshold table se seedha liya gaya
// framing: >=90% confidence wale fields auto-approve honeyogya hain
// (85.7% STP rate, 2.52% error rate uss table me), baaki review ke liye
// flag hote hain. Yahi 3-bucket split UI me bhi dikhta hai.
export type ConfidenceTier = "auto" | "review" | "low";

export function confidenceTier(confidence: number): ConfidenceTier {
  if (confidence >= STP_CONFIDENCE_THRESHOLD) return "auto";
  if (confidence >= 0.7) return "review";
  return "low";
}

export const confidenceTierStyles: Record<ConfidenceTier, string> = {
  auto: "bg-[var(--color-emerald-glow)]/10 text-[var(--color-emerald-glow)] ring-[var(--color-emerald-glow)]/25",
  review: "bg-[var(--color-amber-glow)]/10 text-[var(--color-amber-glow)] ring-[var(--color-amber-glow)]/25",
  low: "bg-[var(--color-rose-glow)]/10 text-[var(--color-rose-glow)] ring-[var(--color-rose-glow)]/25",
};

// Visual bar fill color per tier, used by the confidence-bar UI (a bar
// communicates "how strong is the evidence" more honestly than a bare
// badge — matches the "confidence is evidence, not certainty" framing).
export const confidenceTierBar: Record<ConfidenceTier, string> = {
  auto: "bg-[var(--color-emerald-glow)]",
  review: "bg-[var(--color-amber-glow)]",
  low: "bg-[var(--color-rose-glow)]",
};

export const confidenceTierLabel: Record<ConfidenceTier, string> = {
  auto: "Auto-approve",
  review: "Review",
  low: "Needs review",
};

// Shown behind an info icon next to every confidence number - explains what
// the percentage actually means (calibrated probability, not a vibe), sourced
// from the same Phase 6 calibration + STP-threshold numbers as the badges
// above, so the explanation and the behavior never drift apart.
export const CONFIDENCE_EXPLAINER =
  "Calibrated, not guessed: when this says 90%, the model is right about 90% of the time on held-out test data. 90%+ auto-approves, 70-89% gets a quick human check, below 70% is flagged for review.";
