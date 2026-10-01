import { useEffect, useRef } from "react";
import gsap from "gsap";
import { MagneticButton } from "../ui/MagneticButton";
import { RevealText } from "../ui/RevealText";
import { REAL_OCR_GARBAGE, STP_HEADLINE } from "../../lib/metrics";

const CLEAN_FIELDS = [
  { label: "VENDOR", value: "City Enterprises" },
  { label: "GSTIN", value: "091GQTQ1444X1Z7" },
  { label: "INVOICE NO", value: "INV-5072" },
  { label: "DATE", value: "25/05/2026" },
  { label: "TOTAL", value: "₹7,104.35" },
];

/**
 * The hero's central visual: real garbage OCR strings (from results-log.md's
 * Baseline A diagnostic - genuinely what Tesseract produced on hard
 * receipts) scattered and rotated, settling/fading as a clean structured
 * field card fades in on top. Not a generic 3D blob - it's a literal,
 * honest picture of what this product actually does.
 */
function ConvergenceVisual() {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".chaos-frag",
        { opacity: 0.8, scale: 1 },
        {
          opacity: 0,
          scale: 0.8,
          duration: 1.2,
          ease: "power2.inOut",
          stagger: 0.06,
          delay: 1.4,
        },
      );
      gsap.fromTo(
        ".clean-card",
        { opacity: 0, y: 16, scale: 0.97 },
        { opacity: 1, y: 0, scale: 1, duration: 0.9, ease: "power3.out", delay: 1.9 },
      );
      gsap.fromTo(
        ".clean-row",
        { opacity: 0, x: -8 },
        { opacity: 1, x: 0, duration: 0.5, stagger: 0.08, delay: 2.2, ease: "power2.out" },
      );
    }, rootRef);
    return () => ctx.revert();
  }, []);

  const fragments = [...REAL_OCR_GARBAGE, "0Ca5h", "INV-4|27", "GSTlN: ??", "rT a", "= eGan"];

  return (
    <div ref={rootRef} className="relative h-[380px] w-full max-w-sm">
      {fragments.map((f, i) => (
        <span
          key={i}
          className="chaos-frag font-data absolute select-none whitespace-nowrap text-sm text-[var(--color-paper-600)]"
          style={{
            top: `${(i * 37) % 340}px`,
            left: `${(i * 53) % 220}px`,
            transform: `rotate(${(i % 5) * 6 - 12}deg)`,
          }}
        >
          {f}
        </span>
      ))}

      <div className="clean-card absolute inset-0 flex flex-col justify-center rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)]/95 p-6 opacity-0 shadow-2xl shadow-black/40 backdrop-blur">
        <p className="text-[11px] uppercase tracking-widest text-[var(--color-brass-400)]">Extracted</p>
        <div className="mt-4 space-y-3">
          {CLEAN_FIELDS.map((f) => (
            <div key={f.label} className="clean-row flex items-center justify-between opacity-0">
              <span className="text-[11px] uppercase tracking-wide text-[var(--color-paper-600)]">{f.label}</span>
              <span className="font-data text-sm text-[var(--color-paper-50)]">{f.value}</span>
            </div>
          ))}
        </div>
        <div className="clean-row mt-5 flex items-center gap-2 border-t border-[var(--color-ink-600)] pt-4 opacity-0">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-emerald-glow)]" />
          <span className="text-xs text-[var(--color-paper-400)]">
            {STP_HEADLINE.autoApprovePct}% of fields auto-approve at {STP_HEADLINE.threshold}% confidence
          </span>
        </div>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section id="top" className="grain relative flex min-h-screen items-center overflow-hidden pt-24">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 30% 20%, color-mix(in srgb, var(--color-brass-500) 18%, transparent), transparent)",
        }}
      />
      <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-16 px-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--color-ink-600)] px-3 py-1 text-xs text-[var(--color-paper-400)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-brass-400)]" />
            Document Intelligence
          </p>
          <RevealText
            as="h1"
            trigger="load"
            className="font-display text-6xl font-semibold leading-[0.98] tracking-tight text-[var(--color-paper-50)] sm:text-7xl lg:text-[5.5rem]"
          >
            Messy scans. Clean fields.
          </RevealText>
          <p className="mt-8 max-w-md text-lg leading-relaxed text-[var(--color-paper-400)]">
            Chalan reads invoices and receipts the way a person would — vendor, GSTIN, dates, line
            items, totals — then tells you exactly how sure it is about every single field.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <MagneticButton href="/app" cursorText="TRY IT" variant="solid">
              Open the workspace
            </MagneticButton>
            <MagneticButton href="#pipeline" cursorText="SCROLL" variant="ghost">
              See how it works
            </MagneticButton>
          </div>
        </div>
        <div className="flex justify-center lg:justify-end">
          <ConvergenceVisual />
        </div>
      </div>
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 text-[var(--color-paper-600)]">
        <div className="flex flex-col items-center gap-2">
          <span className="text-[10px] uppercase tracking-[0.2em]">Scroll</span>
          <span className="h-8 w-px animate-pulse bg-[var(--color-ink-500)]" />
        </div>
      </div>
    </section>
  );
}
