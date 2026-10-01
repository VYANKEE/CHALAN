import { useEffect } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

/**
 * Smooth-scroll setup shared by any page that wants the cinematic feel
 * (currently just Landing — the Workspace app stays on native scroll since
 * it's a data-dense tool, not a story, and native scroll is what people
 * expect when reading/reviewing a table of jobs).
 *
 * Wires Lenis's frame loop into GSAP's ticker so ScrollTrigger stays in
 * sync with the smoothed scroll position instead of the raw one - without
 * this, pinned/scrubbed sections drift out of alignment with the pointer.
 * Respects prefers-reduced-motion by skipping smoothing entirely (native
 * scroll, ScrollTrigger still works, just no smoothing layer on top).
 */
export function useLenis() {
  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) return;

    const lenis = new Lenis({
      duration: 1.1,
      smoothWheel: true,
    });

    lenis.on("scroll", ScrollTrigger.update);

    gsap.ticker.add((time) => {
      lenis.raf(time * 1000);
    });
    gsap.ticker.lagSmoothing(0);

    return () => {
      lenis.destroy();
      gsap.ticker.remove((time) => lenis.raf(time * 1000));
    };
  }, []);
}
