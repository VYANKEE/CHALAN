import { useEffect, useRef } from "react";
import gsap from "gsap";
import { STAGE_LABELS, STAGE_ORDER } from "../../lib/metrics";
import type { Job, JobStage } from "../../lib/types";

interface Props {
  jobs: Job[];
  batchIds: string[];
  /** Called once every job in the batch has reached done/failed, with the
   * first successfully-done job's id (or null if the whole batch failed) so
   * the caller can auto-open it. */
  onDone: (firstDoneId: string | null) => void;
  /** Called if the person closes the overlay early - dismiss without
   * auto-opening anything, the list underneath keeps updating live either way. */
  onSkip: () => void;
}

function displayStage(job: Job): JobStage | "queued" {
  if (job.status === "done") return "done";
  if (job.status === "failed") return "failed";
  return job.stage ?? "queued";
}

/**
 * Full-screen "your documents are being read" moment. Every stage shown
 * here is real, not a timed/branded animation: tasks.py pushes "queued" the
 * instant the Celery worker picks a job up, then inference.py's on_stage
 * callback pushes "ocr" / "model" / "decoding" right before each of those
 * pipeline steps actually runs (see status_bus.py's publish_status
 * docstring for the full contract). Each document gets its own card,
 * rendered in parallel with every other in-flight document, each driven
 * only by that document's own live stage - a single upload shows one card,
 * a batch shows all of them updating independently and simultaneously.
 */
export function ProcessingOverlay({ jobs, batchIds, onDone, onSkip }: Props) {
  const batchJobs = batchIds.map((id) => jobs.find((j) => j.id === id)).filter((j): j is Job => Boolean(j));
  const doneCount = batchJobs.filter((j) => j.status === "done" || j.status === "failed").length;
  const allTerminal = batchJobs.length > 0 && doneCount === batchJobs.length;
  const failedCount = batchJobs.filter((j) => j.status === "failed").length;

  const checkRef = useRef<SVGSVGElement>(null);
  const firedRef = useRef(false);

  // Checkmark celebration once everything lands, then auto-dismiss.
  useEffect(() => {
    if (!allTerminal || firedRef.current) return;
    firedRef.current = true;
    if (checkRef.current) {
      gsap.fromTo(
        checkRef.current,
        { scale: 0.5, opacity: 0, rotate: -15 },
        { scale: 1, opacity: 1, rotate: 0, duration: 0.5, ease: "back.out(2.2)" },
      );
    }
    const firstDone = batchJobs.find((j) => j.status === "done");
    const t = setTimeout(() => onDone(firstDone?.id ?? null), 1150);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allTerminal]);

  if (batchJobs.length === 0) return null;

  return (
    <div className="grain fixed inset-0 z-[100] flex flex-col items-center overflow-y-auto bg-[var(--color-ink-950)]/97 px-6 py-10 backdrop-blur-sm sm:justify-center">
      <button
        type="button"
        onClick={onSkip}
        aria-label="Close"
        data-cursor="CLOSE"
        className="fixed right-6 top-6 flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-paper-600)] transition-colors hover:bg-[var(--color-ink-800)] hover:text-[var(--color-paper-50)]"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>

      <div className="w-full max-w-4xl">
        <div className="flex flex-col items-center text-center">
          {!allTerminal ? (
            <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-900)]">
              <span className="absolute inset-0 animate-ping rounded-2xl bg-[var(--color-brass-400)]/10" />
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-brass-400)" strokeWidth="1.6">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
          ) : (
            <div
              className={`flex h-16 w-16 items-center justify-center rounded-2xl border ${
                failedCount > 0
                  ? "border-[var(--color-amber-glow)]/40 bg-[var(--color-amber-glow)]/10"
                  : "border-[var(--color-emerald-glow)]/40 bg-[var(--color-emerald-glow)]/10"
              }`}
            >
              <svg
                ref={checkRef}
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke={failedCount > 0 ? "var(--color-amber-glow)" : "var(--color-emerald-glow)"}
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
          )}

          <h2 className="font-display mt-6 text-2xl font-semibold text-[var(--color-paper-50)] sm:text-3xl">
            {allTerminal
              ? failedCount > 0
                ? `Done — ${failedCount} of ${batchJobs.length} needs a look`
                : "All done"
              : batchJobs.length > 1
                ? `Reading ${batchJobs.length} documents…`
                : "Reading your document…"}
          </h2>
          <p className="mt-2 text-sm text-[var(--color-paper-400)]">
            {allTerminal
              ? "Opening the results…"
              : batchJobs.length > 1
                ? "Every document below is moving through the pipeline on its own"
                : "OCR, then the model, then field extraction — live below"}
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {batchJobs.map((job) => (
            <DocumentProgressCard key={job.id} job={job} />
          ))}
        </div>
      </div>
    </div>
  );
}

function DocumentProgressCard({ job }: { job: Job }) {
  const scanRef = useRef<HTMLDivElement>(null);
  const stage = displayStage(job);
  const failed = job.status === "failed";
  const done = job.status === "done";
  const terminal = failed || done;
  const stageIndex = STAGE_ORDER.indexOf(stage as (typeof STAGE_ORDER)[number]);

  // Per-card scan-line - each document animates completely independently of
  // every other card, so a batch genuinely shows them all in parallel.
  useEffect(() => {
    if (!scanRef.current || terminal) return;
    const tween = gsap.fromTo(
      scanRef.current,
      { y: 2 },
      { y: 46, duration: 1.3, repeat: -1, yoyo: true, ease: "sine.inOut" },
    );
    return () => {
      tween.kill();
    };
  }, [terminal]);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border p-4 transition-colors duration-500 ${
        failed
          ? "border-[var(--color-rose-glow)]/30 bg-[var(--color-rose-glow)]/5"
          : done
            ? "border-[var(--color-emerald-glow)]/30 bg-[var(--color-emerald-glow)]/5"
            : "border-[var(--color-ink-600)] bg-[var(--color-ink-900)]"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="relative flex h-11 w-11 flex-shrink-0 items-center justify-center overflow-hidden rounded-xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)]">
          {!terminal && (
            <div
              ref={scanRef}
              aria-hidden="true"
              className="pointer-events-none absolute inset-x-1 h-[2px] rounded-full"
              style={{
                background: "linear-gradient(90deg, transparent, var(--color-brass-400), transparent)",
                boxShadow: "0 0 8px 1px var(--color-brass-400)",
              }}
            />
          )}
          {failed ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-rose-glow)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ) : done ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-emerald-glow)" strokeWidth="2.2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-brass-400)" strokeWidth="1.6">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-[var(--color-paper-50)]">{job.filename}</p>
          <p
            className={`truncate text-xs ${
              failed ? "text-[var(--color-rose-glow)]" : done ? "text-[var(--color-emerald-glow)]" : "text-[var(--color-brass-300)]"
            }`}
          >
            {failed ? (job.error ?? "Failed") : (STAGE_LABELS[stage] ?? stage)}
          </p>
        </div>
      </div>

      {!failed && (
        <div className="mt-3 flex items-center gap-1">
          {STAGE_ORDER.map((s, i) => (
            <div
              key={s}
              className="h-1 flex-1 rounded-full transition-colors duration-500"
              style={{
                background:
                  i < stageIndex || done
                    ? "var(--color-emerald-glow)"
                    : i === stageIndex
                      ? "var(--color-brass-400)"
                      : "var(--color-ink-600)",
                boxShadow: i === stageIndex && !done ? "0 0 6px 0 var(--color-brass-400)" : "none",
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
