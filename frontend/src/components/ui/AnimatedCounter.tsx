import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface Props {
  value: number;
  decimals?: number;
  suffix?: string;
  className?: string;
}

/** Counts up from 0 to `value` once the element scrolls into view. Purely
 * presentational - the value itself always comes from metrics.ts (real
 * measured numbers), this component never invents what it animates to. */
export function AnimatedCounter({ value, decimals = 0, suffix = "", className = "" }: Props) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const counter = { n: 0 };
    const trigger = ScrollTrigger.create({
      trigger: el,
      start: "top 85%",
      once: true,
      onEnter: () => {
        gsap.to(counter, {
          n: value,
          duration: 1.4,
          ease: "power2.out",
          onUpdate: () => {
            el.textContent = counter.n.toFixed(decimals) + suffix;
          },
        });
      },
    });
    return () => trigger.kill();
  }, [value, decimals, suffix]);

  return (
    <span ref={ref} className={className}>
      0{suffix}
    </span>
  );
}
