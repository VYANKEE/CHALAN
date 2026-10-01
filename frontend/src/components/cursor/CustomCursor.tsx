import { useEffect, useRef } from "react";
import gsap from "gsap";

/**
 * Premium custom cursor - dot + lagging ring, ring expands and can show
 * contextual text on any element with data-cursor="TEXT". Only ever active
 * on a fine-pointer, non-touch, no-reduced-motion desktop: everything else
 * (phones, tablets, trackpad-only touch laptops, anyone who asked their OS
 * for reduced motion) keeps the real system cursor untouched. The gate is
 * a media query, not a screen-width guess, so it's correct on a touch
 * laptop at desktop width too.
 */
export function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const labelRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!canHover || reduceMotion) return;

    document.documentElement.classList.add("custom-cursor");

    const dot = dotRef.current!;
    const ring = ringRef.current!;

    const moveDot = gsap.quickTo(dot, "x", { duration: 0.05, ease: "power3.out" });
    const moveDotY = gsap.quickTo(dot, "y", { duration: 0.05, ease: "power3.out" });
    const moveRing = gsap.quickTo(ring, "x", { duration: 0.35, ease: "power3.out" });
    const moveRingY = gsap.quickTo(ring, "y", { duration: 0.35, ease: "power3.out" });

    function onMove(e: MouseEvent) {
      moveDot(e.clientX);
      moveDotY(e.clientY);
      moveRing(e.clientX);
      moveRingY(e.clientY);
    }

    function onOver(e: MouseEvent) {
      const target = (e.target as HTMLElement)?.closest<HTMLElement>("[data-cursor]");
      if (!target) return;
      const text = target.getAttribute("data-cursor") || "";
      gsap.to(ring, { width: text ? 76 : 56, height: text ? 76 : 56, opacity: 1, duration: 0.25 });
      gsap.to(dot, { scale: 0, duration: 0.2 });
      if (labelRef.current) labelRef.current.textContent = text;
    }

    function onOut(e: MouseEvent) {
      const target = (e.target as HTMLElement)?.closest<HTMLElement>("[data-cursor]");
      if (!target) return;
      gsap.to(ring, { width: 40, height: 40, opacity: 0.6, duration: 0.25 });
      gsap.to(dot, { scale: 1, duration: 0.2 });
      if (labelRef.current) labelRef.current.textContent = "";
    }

    window.addEventListener("mousemove", onMove);
    document.addEventListener("mouseover", onOver);
    document.addEventListener("mouseout", onOut);

    return () => {
      document.documentElement.classList.remove("custom-cursor");
      window.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseover", onOver);
      document.removeEventListener("mouseout", onOut);
    };
  }, []);

  return (
    <>
      <div ref={dotRef} className="cursor-dot" aria-hidden="true" />
      <div ref={ringRef} className="cursor-ring" aria-hidden="true">
        <span ref={labelRef} />
      </div>
    </>
  );
}
