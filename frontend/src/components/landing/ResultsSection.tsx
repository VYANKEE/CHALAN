import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { RevealText } from "../ui/RevealText";
import { AnimatedCounter } from "../ui/AnimatedCounter";
import {
  ACCURACY_PROGRESSION,
  GPU_VS_CPU_SPEEDUP,
  LATENCY,
  QUANTIZATION_ACCURACY_COST,
  QUANTIZATION_SHRINK,
  STP_HEADLINE,
} from "../../lib/metrics";

gsap.registerPlugin(ScrollTrigger);

function AccuracyBars() {
  const ref = useRef<HTMLDivElement>(null);
  const max = Math.max(...ACCURACY_PROGRESSION.map((s) => s.value));

  useEffect(() => {
    const bars = gsap.utils.toArray<HTMLElement>(".accuracy-fill", ref.current!);
    const st = ScrollTrigger.create({
      trigger: ref.current,
      start: "top 80%",
      once: true,
      onEnter: () => {
        bars.forEach((bar) => {
          const target = bar.dataset.width;
          gsap.to(bar, { width: target, duration: 1.1, ease: "power3.out" });
        });
      },
    });
    return () => st.kill();
  }, []);

  return (
    <div ref={ref} className="space-y-5">
      {ACCURACY_PROGRESSION.map((stage, i) => (
        <div key={stage.label}>
          <div className="mb-1.5 flex items-baseline justify-between">
            <div>
              <span className="text-sm font-medium text-[var(--color-paper-50)]">{stage.label}</span>
              <span className="ml-2 text-xs text-[var(--color-paper-600)]">{stage.sub}</span>
            </div>
            <span className="font-data text-sm text-[var(--color-brass-300)]">{stage.value}%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-[var(--color-ink-700)]">
            <div
              className="accuracy-fill h-full rounded-full"
              data-width={`${(stage.value / max) * 100}%`}
              style={{
                width: 0,
                background:
                  i === ACCURACY_PROGRESSION.length - 1
                    ? "linear-gradient(90deg, var(--color-brass-500), var(--color-brass-300))"
                    : "var(--color-ink-500)",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ResultsSection() {
  const fastest = LATENCY[0];
  const cpuBaseline = LATENCY[1];

  return (
    <section id="results" className="border-t border-[var(--color-ink-700)] py-32">
      <div className="mx-auto max-w-6xl px-6">
        <p className="mb-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">Measured, not marketed</p>
        <RevealText
          as="h2"
          className="font-display max-w-2xl text-4xl font-semibold leading-tight tracking-tight text-[var(--color-paper-50)] sm:text-5xl"
        >
          Every number on this page is from a real evaluation run.
        </RevealText>

        <div className="mt-16 grid grid-cols-1 gap-16 lg:grid-cols-2">
          <div>
            <p className="mb-6 text-sm font-medium text-[var(--color-paper-200)]">
              Field-extraction accuracy, baseline to fine-tuned
            </p>
            <AccuracyBars />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 rounded-2xl border border-[var(--color-brass-500)]/25 bg-[var(--color-brass-400)]/5 p-6">
              <p className="text-[11px] uppercase tracking-widest text-[var(--color-brass-400)]">
                Straight-through processing
              </p>
              <div className="mt-2 flex items-baseline gap-2">
                <AnimatedCounter
                  value={STP_HEADLINE.autoApprovePct}
                  decimals={1}
                  suffix="%"
                  className="font-data text-5xl font-semibold text-[var(--color-paper-50)]"
                />
                <span className="text-sm text-[var(--color-paper-400)]">auto-approved</span>
              </div>
              <p className="mt-2 text-sm text-[var(--color-paper-400)]">
                at a {STP_HEADLINE.threshold}% confidence threshold, with a{" "}
                <span className="text-[var(--color-paper-200)]">{STP_HEADLINE.errorPct}% error rate</span> among
                those — a human only needs to touch the rest.
              </p>
            </div>

            <div className="rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)] p-6">
              <p className="text-[11px] uppercase tracking-widest text-[var(--color-paper-600)]">GPU inference</p>
              <p className="font-data mt-2 text-3xl font-semibold text-[var(--color-paper-50)]">
                {fastest.ms}<span className="text-base text-[var(--color-paper-600)]">ms</span>
              </p>
              <p className="mt-2 text-xs text-[var(--color-paper-400)]">
                {GPU_VS_CPU_SPEEDUP} faster than CPU ({cpuBaseline.ms.toFixed(0)}ms)
              </p>
            </div>

            <div className="rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)] p-6">
              <p className="text-[11px] uppercase tracking-widest text-[var(--color-paper-600)]">INT8 quantization</p>
              <p className="font-data mt-2 text-3xl font-semibold text-[var(--color-paper-50)]">
                {QUANTIZATION_SHRINK}<span className="text-base text-[var(--color-paper-600)]"> smaller</span>
              </p>
              <p className="mt-2 text-xs text-[var(--color-paper-400)]">
                at a real {QUANTIZATION_ACCURACY_COST}pp accuracy cost — a tradeoff, not a free win
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
