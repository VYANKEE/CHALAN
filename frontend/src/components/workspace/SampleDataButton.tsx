import { sampleDataUrl } from "../../lib/api";

/**
 * Core UX requirement #2: a recruiter/interviewer trying the demo without
 * their own receipt photo gets a one-click sample bundle. If the backend
 * bundle isn't built yet, `/sample-data` 404s - that's a real, documented
 * gap (project-plan.md), not hidden here.
 */
export function SampleDataButton() {
  return (
    <a
      href={sampleDataUrl()}
      download
      data-cursor="GET"
      className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-ink-500)] bg-[var(--color-ink-800)] px-3 py-2 text-sm font-medium text-[var(--color-paper-200)] transition-colors hover:border-[var(--color-brass-400)]/60 hover:text-[var(--color-brass-300)]"
    >
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      Download sample data
    </a>
  );
}
