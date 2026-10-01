import { useRef, useState } from "react";
import gsap from "gsap";
import { deleteJob } from "../../lib/api";
import { JobDetail } from "./JobDetail";
import { StatusBadge } from "./StatusBadge";
import { STAGE_LABELS } from "../../lib/metrics";
import type { Job } from "../../lib/types";

interface Props {
  job: Job;
  expanded: boolean;
  onToggle: () => void;
  onDeleted: (jobId: string) => void;
  onReviewUpdate: (jobId: string, updatedJob: Job) => void;
}

export function JobRow({ job, expanded, onToggle, onDeleted, onReviewUpdate }: Props) {
  const canExpand = job.status === "done" || job.status === "failed";
  const [deleting, setDeleting] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (deleting) return;
    setDeleting(true);
    try {
      await deleteJob(job.id);
      const el = rootRef.current;
      if (el) {
        await gsap.to(el, { opacity: 0, height: 0, marginBottom: 0, duration: 0.3, ease: "power2.in" });
      }
      onDeleted(job.id);
    } catch {
      setDeleting(false);
    }
  }

  return (
    <div
      ref={rootRef}
      id={`job-${job.id}`}
      className="overflow-hidden rounded-xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)] transition-colors hover:border-[var(--color-ink-500)]"
    >
      <div className="flex w-full items-center justify-between gap-3 px-4 py-3">
        <button
          type="button"
          onClick={onToggle}
          disabled={!canExpand}
          data-cursor={canExpand ? "VIEW" : ""}
          className={`flex min-w-0 flex-1 items-center gap-3 text-left ${
            canExpand ? "cursor-pointer" : "cursor-default"
          }`}
        >
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--color-ink-700)] text-[var(--color-paper-400)]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-[var(--color-paper-50)]">{job.filename}</p>
            <p className="text-xs text-[var(--color-paper-600)]">
              {job.status === "processing" && job.stage
                ? (STAGE_LABELS[job.stage] ?? "Processing…")
                : new Date(job.created_at).toLocaleTimeString()}
            </p>
          </div>
        </button>
        <div className="flex flex-shrink-0 items-center gap-3">
          <StatusBadge status={job.status} />
          {canExpand && (
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              aria-label="Delete this upload"
              data-cursor="DELETE"
              className="flex h-7 w-7 items-center justify-center rounded-lg text-[var(--color-paper-600)] transition-colors hover:bg-[var(--color-rose-glow)]/10 hover:text-[var(--color-rose-glow)] disabled:opacity-50"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          )}
          {canExpand && (
            <button type="button" onClick={onToggle} data-cursor="VIEW" aria-label="Expand">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={`text-[var(--color-paper-600)] transition-transform ${expanded ? "rotate-180" : ""}`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          )}
        </div>
      </div>
      {expanded && canExpand && (
        <div className="border-t border-[var(--color-ink-600)] px-4 py-3">
          <JobDetail job={job} onReviewUpdate={onReviewUpdate} />
        </div>
      )}
    </div>
  );
}
