import { useState } from "react";
import { submitReview } from "../../lib/api";
import type { Job, ReviewNote } from "../../lib/types";

interface Props {
  job: Job;
  fieldKey: string;
  note: ReviewNote | undefined;
  onUpdated: (jobId: string, updatedJob: Job) => void;
}

/**
 * Human-in-the-loop action for one non-auto-approved field: leave a comment
 * and either flag it onward to the review team or mark it resolved yourself.
 * Only rendered under fields that aren't already auto-approved (Core UX:
 * a human only ever touches what the model was genuinely unsure about).
 */
export function ReviewRow({ job, fieldKey, note, onUpdated }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState<"sent" | "resolved" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(action: "sent" | "resolved") {
    setSubmitting(action);
    setError(null);
    try {
      const updated = await submitReview(job.id, fieldKey, comment.trim(), action);
      onUpdated(job.id, updated);
      setComment("");
      setExpanded(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save.");
    } finally {
      setSubmitting(null);
    }
  }

  if (note && !expanded) {
    const isSent = note.status === "sent";
    return (
      <button
        type="button"
        onClick={() => {
          setComment(note.comment);
          setExpanded(true);
        }}
        data-cursor="EDIT"
        className="mt-2 flex w-full items-center gap-2 rounded-lg border border-[var(--color-ink-600)] bg-[var(--color-ink-950)] px-3 py-2 text-left text-xs transition-colors hover:border-[var(--color-ink-500)]"
      >
        <span
          className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${
            isSent ? "bg-[var(--color-amber-glow)]" : "bg-[var(--color-emerald-glow)]"
          }`}
        />
        <span className={isSent ? "text-[var(--color-amber-glow)]" : "text-[var(--color-emerald-glow)]"}>
          {isSent ? "Sent to review team" : "Marked resolved"}
        </span>
        {note.comment && (
          <span className="min-w-0 flex-1 truncate text-[var(--color-paper-400)]">— {note.comment}</span>
        )}
        <span className="flex-shrink-0 text-[var(--color-paper-600)]">Edit</span>
      </button>
    );
  }

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        data-cursor="NOTE"
        className="mt-2 text-xs font-medium text-[var(--color-paper-600)] transition-colors hover:text-[var(--color-brass-300)]"
      >
        + Add review note
      </button>
    );
  }

  return (
    <div className="mt-2 rounded-lg border border-[var(--color-ink-600)] bg-[var(--color-ink-950)] p-3">
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="What did you notice about this field?"
        rows={2}
        autoFocus
        className="w-full resize-none rounded-md border border-[var(--color-ink-600)] bg-[var(--color-ink-900)] px-2.5 py-2 text-xs text-[var(--color-paper-50)] placeholder:text-[var(--color-paper-600)] focus:border-[var(--color-brass-400)] focus:outline-none"
      />
      {error && <p className="mt-1.5 text-[11px] text-[var(--color-rose-glow)]">{error}</p>}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => submit("sent")}
          disabled={submitting !== null}
          data-cursor="SEND"
          className="inline-flex items-center gap-1.5 rounded-md bg-[var(--color-amber-glow)]/10 px-2.5 py-1.5 text-[11px] font-medium text-[var(--color-amber-glow)] ring-1 ring-inset ring-[var(--color-amber-glow)]/25 transition-opacity hover:opacity-80 disabled:opacity-50"
        >
          {submitting === "sent" ? "Sending…" : "Send to review team"}
        </button>
        <button
          type="button"
          onClick={() => submit("resolved")}
          disabled={submitting !== null}
          data-cursor="DONE"
          className="inline-flex items-center gap-1.5 rounded-md bg-[var(--color-emerald-glow)]/10 px-2.5 py-1.5 text-[11px] font-medium text-[var(--color-emerald-glow)] ring-1 ring-inset ring-[var(--color-emerald-glow)]/25 transition-opacity hover:opacity-80 disabled:opacity-50"
        >
          {submitting === "resolved" ? "Saving…" : "Mark resolved"}
        </button>
        <button
          type="button"
          onClick={() => {
            setExpanded(false);
            setError(null);
          }}
          disabled={submitting !== null}
          className="ml-auto text-[11px] text-[var(--color-paper-600)] transition-colors hover:text-[var(--color-paper-400)]"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
