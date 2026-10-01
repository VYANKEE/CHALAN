import { useRef } from "react";
import type { ReactNode, MouseEvent as ReactMouseEvent } from "react";
import gsap from "gsap";

interface Props {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
  variant?: "solid" | "ghost";
  cursorText?: string;
  className?: string;
}

/**
 * Button with a magnetic hover pull (desktop only, in practice - on touch
 * there's no hover event to trigger it, so it degrades to a plain button
 * automatically without any extra branching needed here).
 */
export function MagneticButton({ children, onClick, href, variant = "solid", cursorText, className = "" }: Props) {
  const ref = useRef<HTMLAnchorElement | HTMLButtonElement>(null);

  function onMouseMove(e: ReactMouseEvent) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    gsap.to(el, { x: x * 0.35, y: y * 0.35, duration: 0.4, ease: "power3.out" });
  }

  function onMouseLeave() {
    gsap.to(ref.current, { x: 0, y: 0, duration: 0.5, ease: "elastic.out(1, 0.4)" });
  }

  const base =
    "relative inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium tracking-tight transition-colors duration-200";
  const styles =
    variant === "solid"
      ? "bg-[var(--color-brass-400)] text-[var(--color-ink-950)] hover:bg-[var(--color-brass-300)]"
      : "border border-[var(--color-ink-500)] text-[var(--color-paper-50)] hover:border-[var(--color-brass-400)] hover:text-[var(--color-brass-300)]";

  const commonProps = {
    onMouseMove,
    onMouseLeave,
    onClick,
    "data-cursor": cursorText ?? "",
    className: `${base} ${styles} ${className}`,
  };

  if (href) {
    return (
      <a ref={ref as React.RefObject<HTMLAnchorElement>} href={href} {...commonProps}>
        {children}
      </a>
    );
  }

  return (
    <button ref={ref as React.RefObject<HTMLButtonElement>} type="button" {...commonProps}>
      {children}
    </button>
  );
}
