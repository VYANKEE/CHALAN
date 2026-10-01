import { RevealText } from "../ui/RevealText";
import { AnimatedCounter } from "../ui/AnimatedCounter";
import { REAL_OCR_GARBAGE } from "../../lib/metrics";

export function ProblemSection() {
  return (
    <section className="border-t border-[var(--color-ink-700)] bg-[var(--color-ink-900)] py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-1 gap-16 lg:grid-cols-2">
          <div>
            <p className="mb-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">The problem</p>
            <RevealText
              as="h2"
              className="font-display text-4xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-5xl"
            >
              A human keys in every invoice. That's the whole industry.
            </RevealText>
            <p className="mt-6 max-w-md text-[var(--color-paper-400)]">
              Low-res phone photos. Faded thermal-printer ink. Skewed angles, inconsistent
              lighting. Plain OCR + a regex for "total" — the obvious first approach — genuinely
              breaks on this data, not as a strawman, but as a measured result.
            </p>
            <div className="mt-10 flex items-end gap-3">
              <AnimatedCounter
                value={2.0}
                decimals={1}
                suffix="%"
                className="font-data text-6xl font-semibold text-[var(--color-rose-glow)]"
              />
              <span className="mb-2 text-sm text-[var(--color-paper-600)]">
                exact-match accuracy —
                <br />
                OCR + regex rules, measured on 100 real receipts
              </span>
            </div>
          </div>

          <div className="flex flex-col justify-center gap-3 rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-950)] p-6 font-data text-sm">
            <p className="mb-2 text-[11px] uppercase tracking-widest text-[var(--color-paper-600)]">
              Real Tesseract output, hard receipts
            </p>
            {REAL_OCR_GARBAGE.map((g, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-[var(--color-ink-700)] bg-[var(--color-ink-900)] px-4 py-3"
              >
                <span className="text-[var(--color-rose-glow)]">{g}</span>
                <span className="text-[10px] uppercase tracking-wide text-[var(--color-paper-600)]">unreadable</span>
              </div>
            ))}
            <p className="mt-3 text-xs leading-relaxed text-[var(--color-paper-600)]">
              This is genuine, logged failure output — not a fabricated example of "messy data."
              A regex can't extract a total from text that never came through in the first place.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
