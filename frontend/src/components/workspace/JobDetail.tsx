import { InfoTooltip } from "../ui/InfoTooltip";
import { CONFIDENCE_EXPLAINER, confidenceTier, confidenceTierBar, confidenceTierLabel, confidenceTierStyles } from "../../lib/confidence";
import { ReviewRow } from "./ReviewRow";
import type { Job } from "../../lib/types";

/**
 * Field key "HEADER.VENDOR" -> "Vendor" readable label - the backend's
 * internal BIO-tag naming (load_cord.py LABELS) shouldn't leak into the UI
 * directly. Prefix (HEADER/MENU/SUB_TOTAL/TOTAL) becomes the group heading.
 */
function humanizeField(key: string): { group: string; label: string } {
  const [group, ...rest] = key.split(".");
  const raw = rest.join(" ") || group;
  const label = raw
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
  const groupLabels: Record<string, string> = {
    HEADER: "Header",
    MENU: "Line item",
    SUB_TOTAL: "Subtotal",
    TOTAL: "Total",
  };
  return { group: groupLabels[group] ?? group, label };
}

interface Props {
  job: Job;
  onReviewUpdate: (jobId: string, updatedJob: Job) => void;
}

export function JobDetail({ job, onReviewUpdate }: Props) {
  if (job.status === "queued" || job.status === "processing") {
    return (
      <div className="flex items-center gap-2 px-1 py-6 text-sm text-[var(--color-paper-400)]">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-brass-400)]" />
        {job.status === "queued" ? "Waiting in queue…" : "Extracting fields…"}
      </div>
    );
  }

  if (job.status === "failed") {
    return (
      <div className="rounded-lg bg-[var(--color-rose-glow)]/10 px-4 py-3 text-sm text-[var(--color-rose-glow)]">
        <p className="font-medium">Extraction failed</p>
        <p className="mt-0.5 opacity-80">{job.error}</p>
      </div>
    );
  }

  const entries = Object.entries(job.result?.fields ?? {});
  if (entries.length === 0) {
    return <p className="px-1 py-6 text-sm text-[var(--color-paper-400)]">No fields extracted.</p>;
  }

  const groupOrder = ["HEADER", "MENU", "SUB_TOTAL", "TOTAL"];
  const sorted = [...entries].sort(
    (a, b) => groupOrder.indexOf(a[0].split(".")[0]) - groupOrder.indexOf(b[0].split(".")[0]),
  );

  const autoCount = entries.filter(([, f]) => confidenceTier(f.confidence) === "auto").length;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between px-1">
        <p className="text-xs text-[var(--color-paper-400)]">
          {entries.length} field{entries.length === 1 ? "" : "s"} extracted
        </p>
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-paper-400)]">
          <span>
            <span className="font-medium text-[var(--color-emerald-glow)]">{autoCount}</span> auto-approvable
          </span>
          <InfoTooltip text={CONFIDENCE_EXPLAINER} label="What does confidence mean?" />
        </div>
      </div>
      <div className="divide-y divide-[var(--color-ink-600)] rounded-xl border border-[var(--color-ink-600)] bg-[var(--color-ink-900)]">
        {sorted.map(([key, field]) => {
          const { group, label } = humanizeField(key);
          const tier = confidenceTier(field.confidence);
          const pct = field.confidence * 100;
          return (
            <div key={key} className="px-4 py-3">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] uppercase tracking-wide text-[var(--color-paper-600)]">{group}</p>
                  <p className="truncate text-sm font-medium text-[var(--color-paper-50)]">{label}</p>
                  <p className="font-data mt-0.5 truncate text-sm text-[var(--color-paper-200)]">{field.value}</p>
                </div>
                <div className="flex w-32 flex-shrink-0 flex-col items-end gap-1.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${confidenceTierStyles[tier]}`}
                  >
                    {confidenceTierLabel[tier]}
                  </span>
                  <div className="h-1 w-full overflow-hidden rounded-full bg-[var(--color-ink-700)]">
                    <div
                      className={`h-full rounded-full ${confidenceTierBar[tier]}`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>
                  <span className="font-data text-[11px] text-[var(--color-paper-600)]">{pct.toFixed(1)}%</span>
                </div>
              </div>
              {tier !== "auto" && (
                <ReviewRow job={job} fieldKey={key} note={job.review_notes?.[key]} onUpdated={onReviewUpdate} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
