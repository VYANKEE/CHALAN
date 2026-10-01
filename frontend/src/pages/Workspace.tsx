import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { JobList } from "../components/workspace/JobList";
import { ProcessingOverlay } from "../components/workspace/ProcessingOverlay";
import { SampleDataButton } from "../components/workspace/SampleDataButton";
import { StatsBar } from "../components/workspace/StatsBar";
import { UploadZone } from "../components/workspace/UploadZone";
import { useJobsSocket } from "../hooks/useJobsSocket";
import type { Job } from "../lib/types";

/**
 * The actual working tool - kept on native scroll (unlike Landing) since
 * this is a data-review surface people will scan and act on repeatedly,
 * not a story to scroll through once. Same dark design system as the
 * marketing site (sticky blurred header like Nav.tsx, grain texture, brass
 * accent) so moving from one to the other doesn't feel jarring.
 */
export function Workspace() {
  const { jobs, connected, addJobs, removeJob, patchJob } = useJobsSocket();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  // Ids of the batch currently being watched by the full-screen overlay -
  // cleared once that batch finishes (or the person skips it), independent
  // of jobs that finish quietly in the background afterwards.
  const [batchIds, setBatchIds] = useState<string[]>([]);

  function handleUploaded(newJobs: Job[]) {
    addJobs(newJobs);
    setBatchIds(newJobs.map((j) => j.id));
  }

  function handleOverlayDone(firstDoneId: string | null) {
    setBatchIds([]);
    if (firstDoneId) setExpandedId(firstDoneId);
  }

  function handleDeleted(jobId: string) {
    removeJob(jobId);
    setExpandedId((cur) => (cur === jobId ? null : cur));
  }

  function handleReviewUpdate(jobId: string, updatedJob: Job) {
    patchJob(jobId, updatedJob);
  }

  // Results apne aap samne aana chahiye - once a job auto-expands (fresh
  // upload finishing, or a review update), bring it into view without
  // making the person hunt for it in the list.
  useEffect(() => {
    if (!expandedId) return;
    const el = document.getElementById(`job-${expandedId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [expandedId]);

  return (
    <div className="grain min-h-screen bg-[var(--color-ink-950)]">
      <header className="sticky top-0 z-40 border-b border-[var(--color-ink-700)] bg-[var(--color-ink-950)]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              data-cursor="SITE"
              className="font-display text-lg font-semibold tracking-tight text-[var(--color-paper-50)] transition-colors hover:text-[var(--color-brass-300)]"
            >
              Chalan
            </Link>
            <span className="hidden text-sm text-[var(--color-paper-600)] sm:inline">
              Document Intelligence Workspace
            </span>
          </div>
          <div className="flex flex-shrink-0 items-center gap-1.5 text-xs text-[var(--color-paper-400)]">
            <span
              className={`h-1.5 w-1.5 rounded-full transition-colors ${
                connected ? "bg-[var(--color-emerald-glow)] shadow-[0_0_6px_1px_var(--color-emerald-glow)]" : "bg-[var(--color-ink-500)]"
              }`}
            />
            {connected ? "Live" : "Polling"}
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-4xl px-6 py-10">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-20 left-1/2 h-64 w-[36rem] -translate-x-1/2 rounded-full opacity-[0.07]"
          style={{ background: "radial-gradient(circle, var(--color-brass-400), transparent 70%)" }}
        />

        <div className="relative mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium text-[var(--color-paper-200)]">Upload invoices</h2>
          <SampleDataButton />
        </div>

        <div className="relative">
          <UploadZone onUploaded={handleUploaded} />
        </div>

        <div className="relative mt-8 space-y-4">
          <StatsBar jobs={jobs} />
          <JobList
            jobs={jobs}
            expandedId={expandedId}
            onToggle={(jobId) => setExpandedId((cur) => (cur === jobId ? null : jobId))}
            onDeleted={handleDeleted}
            onReviewUpdate={handleReviewUpdate}
          />
        </div>
      </main>

      {batchIds.length > 0 && (
        <ProcessingOverlay
          jobs={jobs}
          batchIds={batchIds}
          onDone={handleOverlayDone}
          onSkip={() => setBatchIds([])}
        />
      )}
    </div>
  );
}
