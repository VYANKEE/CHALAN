import type { JobStatus } from "../../lib/types";

const styles: Record<JobStatus, string> = {
  queued: "bg-[var(--color-ink-700)] text-[var(--color-paper-400)] ring-[var(--color-ink-500)]",
  processing: "bg-[var(--color-brass-400)]/10 text-[var(--color-brass-300)] ring-[var(--color-brass-400)]/30",
  done: "bg-[var(--color-emerald-glow)]/10 text-[var(--color-emerald-glow)] ring-[var(--color-emerald-glow)]/25",
  failed: "bg-[var(--color-rose-glow)]/10 text-[var(--color-rose-glow)] ring-[var(--color-rose-glow)]/25",
};

const labels: Record<JobStatus, string> = {
  queued: "Queued",
  processing: "Processing",
  done: "Done",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styles[status]}`}
    >
      {status === "processing" && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-brass-400)]" />
      )}
      {labels[status]}
    </span>
  );
}
