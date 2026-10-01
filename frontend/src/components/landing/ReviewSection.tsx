import { RevealText } from "../ui/RevealText";

const STEPS = [
  { n: "01", title: "Model signals", detail: "Every token gets a label and a calibrated probability." },
  { n: "02", title: "Confidence", detail: "Field-level confidence = the weakest token in that field's span." },
  { n: "03", title: "Threshold", detail: "Above the line, auto-approve. Below it, flag for a person." },
  { n: "04", title: "Reviewer", detail: "A human looks only at what the model was genuinely unsure about." },
];

export function ReviewSection() {
  return (
    <section id="review" className="border-t border-[var(--color-ink-700)] py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-2xl">
          <p className="mb-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">Human in the loop</p>
          <RevealText
            as="h2"
            className="font-display text-4xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-5xl"
          >
            The machine finds the field. A person makes the call.
          </RevealText>
          <p className="mt-6 text-[var(--color-paper-400)]">
            Straight-through processing doesn't mean unattended processing. It means a reviewer's
            time goes toward the ~14% of fields the model is actually unsure about, not toward
            re-checking everything from scratch.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-600)] sm:grid-cols-4">
          {STEPS.map((step) => (
            <div key={step.n} className="bg-[var(--color-ink-900)] p-7">
              <span className="font-data text-sm text-[var(--color-brass-400)]">{step.n}</span>
              <h3 className="mt-4 font-display text-xl font-semibold text-[var(--color-paper-50)]">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--color-paper-400)]">{step.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
