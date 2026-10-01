import { confidenceTier } from "../../lib/confidence";
import type { Job } from "../../lib/types";

/**
 * "Command center" stat row - every number here is derived client-side from
 * the real jobs array (same data JobList renders), nothing is a separate
 * fabricated metric. Avg confidence / auto-approved % only exist because
 * the backend's per-field confidence is real (Phase 6 calibration), not a
 * cosmetic dashboard number invented for the redesign.
 */
export function StatsBar({ jobs }: { jobs: Job[] }) {
  const counts = jobs.reduce(
    (acc, job) => {
      acc[job.status] += 1;
      return acc;
    },
    { queued: 0, processing: 0, done: 0, failed: 0 },
  );

  const doneJobs = jobs.filter((j) => j.status === "done" && j.result);
  const allFields = doneJobs.flatMap((j) => Object.values(j.result!.fields));
  const autoApproved = allFields.filter((f) => confidenceTier(f.confidence) === "auto").length;
  const avgConfidence =
    allFields.length > 0
      ? (allFields.reduce((sum, f) => sum + f.confidence, 0) / allFields.length) * 100
      : null;

  if (jobs.length === 0) return null;

  const items = [
    { label: "Documents", value: jobs.length, tone: "text-[var(--color-paper-50)]" },
    { label: "Processing", value: counts.queued + counts.processing, tone: "text-[var(--color-brass-300)]" },
    { label: "Fields auto-approved", value: autoApproved, tone: "text-[var(--color-emerald-glow)]" },
    {
      label: "Avg. confidence",
      value: avgConfidence !== null ? `${avgConfidence.toFixed(1)}%` : "—",
      tone: "text-[var(--color-paper-50)]",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)] px-4 py-3"
        >
          <div className={`font-data text-2xl font-semibold ${item.tone}`}>{item.value}</div>
          <div className="mt-0.5 text-xs text-[var(--color-paper-400)]">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
