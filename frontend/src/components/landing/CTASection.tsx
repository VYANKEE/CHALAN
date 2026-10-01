import { RevealText } from "../ui/RevealText";
import { MagneticButton } from "../ui/MagneticButton";

export function CTASection() {
  return (
    <section className="grain relative overflow-hidden border-t border-[var(--color-ink-700)] py-36 text-center">
      <div
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          background:
            "radial-gradient(ellipse 50% 50% at 50% 40%, color-mix(in srgb, var(--color-brass-500) 20%, transparent), transparent)",
        }}
      />
      <div className="relative mx-auto max-w-2xl px-6">
        <RevealText
          as="h2"
          className="font-display text-5xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-6xl"
        >
          Upload one invoice. See it in under a minute.
        </RevealText>
        <p className="mt-6 text-[var(--color-paper-400)]">
          No signup. Drop a sample receipt, or bring your own — single file or a whole batch.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <MagneticButton href="/app" cursorText="GO">
            Open the workspace
          </MagneticButton>
        </div>
      </div>
    </section>
  );
}
