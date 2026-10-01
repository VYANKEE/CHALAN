import { useEffect, useState } from "react";
import { MagneticButton } from "../ui/MagneticButton";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled ? "border-b border-[var(--color-ink-700)] bg-[var(--color-ink-950)]/80 backdrop-blur-md" : ""
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <a href="#top" data-cursor="TOP" className="font-display text-lg font-semibold tracking-tight text-[var(--color-paper-50)]">
          Chalan
        </a>
        <div className="hidden items-center gap-8 text-sm text-[var(--color-paper-400)] md:flex">
          <a href="#pipeline" className="transition-colors hover:text-[var(--color-paper-50)]">
            How it works
          </a>
          <a href="#results" className="transition-colors hover:text-[var(--color-paper-50)]">
            Results
          </a>
          <a href="#review" className="transition-colors hover:text-[var(--color-paper-50)]">
            Human review
          </a>
        </div>
        <MagneticButton href="/app" cursorText="GO" variant="solid" className="!px-5 !py-2.5 !text-xs">
          Open Workspace
        </MagneticButton>
      </div>
    </nav>
  );
}
