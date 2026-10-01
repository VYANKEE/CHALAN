import { JobRow } from "./JobRow";
import type { Job } from "../../lib/types";

interface Props {
  jobs: Job[];
  expandedId: string | null;
  onToggle: (jobId: string) => void;
  onDeleted: (jobId: string) => void;
  onReviewUpdate: (jobId: string, updatedJob: Job) => void;
}

export function JobList({ jobs, expandedId, onToggle, onDeleted, onReviewUpdate }: Props) {
  if (jobs.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-[var(--color-ink-600)] px-4 py-8 text-center text-sm text-[var(--color-paper-600)]">
        No uploads yet — drop a receipt above to get started.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <JobRow
          key={job.id}
          job={job}
          expanded={expandedId === job.id}
          onToggle={() => onToggle(job.id)}
          onDeleted={onDeleted}
          onReviewUpdate={onReviewUpdate}
        />
      ))}
    </div>
  );
}
