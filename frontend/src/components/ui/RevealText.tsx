import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface Props {
  children: string;
  as?: "h1" | "h2" | "h3" | "p";
  className?: string;
  /** "load" runs once immediately (hero); "scroll" triggers on scroll into view. */
  trigger?: "load" | "scroll";
  delay?: number;
}

/** Splits text into words and reveals them with a staggered clip/opacity/y
 * animation. One reusable primitive used for every big headline on the
 * landing page instead of hand-rolling the same GSAP timeline repeatedly. */
export function RevealText({ children, as = "h2", className = "", trigger = "scroll", delay = 0 }: Props) {
  const ref = useRef<HTMLHeadingElement>(null);
  const Tag = as;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const words = el.querySelectorAll<HTMLElement>(".reveal-word");

    const anim = () =>
      gsap.fromTo(
        words,
        { yPercent: 110, opacity: 0 },
        {
          yPercent: 0,
          opacity: 1,
          duration: 0.9,
          ease: "power4.out",
          stagger: 0.05,
          delay,
        },
      );

    if (trigger === "load") {
      const t = anim();
      return () => {
        t.kill();
      };
    }

    const st = ScrollTrigger.create({
      trigger: el,
      start: "top 85%",
      once: true,
      onEnter: anim,
    });
    return () => st.kill();
  }, [trigger, delay]);

  const words = children.split(" ");

  return (
    <Tag ref={ref as never} className={className}>
      {words.map((w, i) => (
        <span key={i} className="inline-block overflow-hidden pb-1 align-bottom">
          <span className="reveal-word inline-block will-change-transform">
            {w}
            {i < words.length - 1 ? " " : ""}
          </span>
        </span>
      ))}
    </Tag>
  );
}
