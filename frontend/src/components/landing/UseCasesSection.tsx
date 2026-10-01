import { RevealText } from "../ui/RevealText";

const USE_CASES = [
  {
    title: "Accounts payable",
    detail: "Manual invoice entry runs 3-4 minutes per bill at real volume — the actual pain this was built around.",
  },
  {
    title: "GST reconciliation",
    detail: "GSTIN, HSN codes, and the CGST/SGST split extracted as structured fields, not re-typed by hand.",
  },
  {
    title: "Expense capture",
    detail: "A photographed receipt in, a structured, confidence-scored record out — batched or one at a time.",
  },
];

export function UseCasesSection() {
  return (
    <section className="border-t border-[var(--color-ink-700)] bg-[var(--color-ink-900)] py-32">
      <div className="mx-auto max-w-6xl px-6">
        <p className="mb-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">Where this fits</p>
        <RevealText
          as="h2"
          className="font-display max-w-2xl text-4xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-5xl"
        >
          Built for the document that never has a clean template.
        </RevealText>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {USE_CASES.map((uc) => (
            <div
              key={uc.title}
              className="rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-950)] p-7 transition-colors hover:border-[var(--color-brass-500)]/40"
            >
              <h3 className="font-display text-xl font-semibold text-[var(--color-paper-50)]">{uc.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--color-paper-400)]">{uc.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
