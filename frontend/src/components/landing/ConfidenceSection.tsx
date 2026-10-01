import { RevealText } from "../ui/RevealText";
import { CALIBRATION } from "../../lib/metrics";

const SIGNALS = [
  { label: "Vendor", value: 97.4, tier: "auto" as const },
  { label: "GSTIN", value: 93.6, tier: "auto" as const },
  { label: "Invoice No.", value: 99.2, tier: "auto" as const },
  { label: "Line item", value: 25.1, tier: "low" as const },
];

const TIER_COLOR = {
  auto: "var(--color-emerald-glow)",
  review: "var(--color-amber-glow)",
  low: "var(--color-rose-glow)",
};

export function ConfidenceSection() {
  return (
    <section className="border-t border-[var(--color-ink-700)] bg-[var(--color-ink-900)] py-32">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-16 px-6 lg:grid-cols-2">
        <div>
          <p className="mb-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">Confidence, explained</p>
          <RevealText
            as="h2"
            className="font-display text-4xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-5xl"
          >
            97% isn't "definitely right." It's strong evidence.
          </RevealText>
          <p className="mt-6 max-w-md text-[var(--color-paper-400)]">
            Chalan's confidence score is temperature-calibrated (Guo et al., 2017) against a
            held-out test set — Expected Calibration Error dropped from{" "}
            <span className="font-data text-[var(--color-paper-200)]">{CALIBRATION.eceBefore}%</span> to{" "}
            <span className="font-data text-[var(--color-paper-200)]">{CALIBRATION.eceAfter}%</span>. That means
            when it says 90%, it's right roughly 90% of the time — not just loud.
          </p>
          <p className="mt-4 max-w-md text-sm text-[var(--color-paper-600)]">
            One real example: a fitted temperature of T = {CALIBRATION.temperature} — the model came out of
            training already close to well-calibrated, which is unusual and worth stating plainly rather
            than dressing up.
          </p>
        </div>

        <div className="rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-950)] p-7">
          <p className="mb-5 text-[11px] uppercase tracking-widest text-[var(--color-paper-600)]">
            Real fields from one extraction
          </p>
          <div className="space-y-4">
            {SIGNALS.map((s) => (
              <div key={s.label}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-[var(--color-paper-200)]">{s.label}</span>
                  <span className="font-data" style={{ color: TIER_COLOR[s.tier] }}>
                    {s.value}%
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-ink-700)]">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${s.value}%`, background: TIER_COLOR[s.tier] }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-6 border-t border-[var(--color-ink-700)] pt-5 text-xs leading-relaxed text-[var(--color-paper-600)]">
            That last field is a real, honest example — the model briefly mistagged a table header at
            25% confidence. It was correctly flagged for review instead of silently returned as fact. The
            system catching its own uncertain guess is the point of calibration.
          </p>
        </div>
      </div>
    </section>
  );
}
