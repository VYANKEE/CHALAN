import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { PIPELINE_STAGES, TRAINING_EFFICIENCY } from "../../lib/metrics";

gsap.registerPlugin(ScrollTrigger);

/**
 * Pinned horizontal-scroll pipeline walkthrough. Vertical scroll drives
 * horizontal translation of the card track while the section stays pinned -
 * the classic Awwwards "scrollytelling" pattern, built with a plain GSAP
 * tween + ScrollTrigger scrub rather than a library, so it stays legible
 * and debuggable.
 */
export function PipelineSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const track = trackRef.current;
      const container = containerRef.current;
      if (!track || !container) return;

      const setup = () => {
        const distance = track.scrollWidth - window.innerWidth;
        if (distance <= 0) return;
        gsap.to(track, {
          x: -distance,
          ease: "none",
          scrollTrigger: {
            id: "pipeline",
            trigger: container,
            start: "top top",
            end: () => `+=${distance}`,
            scrub: 1,
            pin: true,
            invalidateOnRefresh: true,
          },
        });
      };

      setup();
      const onResize = () => ScrollTrigger.refresh();
      window.addEventListener("resize", onResize);
      return () => window.removeEventListener("resize", onResize);
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section id="pipeline" ref={containerRef} className="relative overflow-hidden bg-[var(--color-ink-950)]">
      <div className="flex h-screen flex-col justify-center">
        <div className="mx-auto mb-10 w-full max-w-6xl px-6">
          <p className="mb-3 text-xs uppercase tracking-[0.2em] text-[var(--color-brass-400)]">How it thinks</p>
          <h2 className="font-display text-4xl font-semibold tracking-tight text-[var(--color-paper-50)] sm:text-5xl">
            Six stages, one field at a time.
          </h2>
        </div>

        <div ref={trackRef} className="flex w-max gap-6 px-6 will-change-transform sm:px-[calc(50vw-20rem)]">
          {PIPELINE_STAGES.map((stage) => (
            <div
              key={stage.n}
              className="pipeline-card flex h-72 w-[22rem] flex-shrink-0 flex-col justify-between rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)] p-7"
            >
              <span className="font-data text-sm text-[var(--color-brass-400)]">{stage.n}</span>
              <div>
                <h3 className="font-display text-2xl font-semibold text-[var(--color-paper-50)]">{stage.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-[var(--color-paper-400)]">{stage.detail}</p>
              </div>
            </div>
          ))}
          <div className="flex h-72 w-[22rem] flex-shrink-0 flex-col justify-center rounded-2xl border border-[var(--color-brass-500)]/30 bg-[var(--color-brass-400)]/5 p-7">
            <p className="text-[11px] uppercase tracking-widest text-[var(--color-brass-400)]">Efficient by design</p>
            <p className="font-data mt-3 text-3xl font-semibold text-[var(--color-paper-50)]">
              {TRAINING_EFFICIENCY.trainablePct}
            </p>
            <p className="mt-2 text-sm text-[var(--color-paper-400)]">
              of the 133M-parameter model was actually trained (LoRA) — the rest stays frozen,
              which is why this fits a {TRAINING_EFFICIENCY.vram} laptop GPU.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
