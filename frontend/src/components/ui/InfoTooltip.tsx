import { useEffect, useRef, useState } from "react";

/**
 * Small "why is this number what it is" affordance - a click-toggle popover
 * (not hover-only, so it works on touch too) rather than a native `title`
 * tooltip, which is invisible on mobile and easy to miss. Closes on an
 * outside click or Escape.
 */
export function InfoTooltip({ text, label = "Why this number" }: { text: string; label?: string }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative inline-flex">
      <button
        type="button"
        aria-label={label}
        data-cursor="INFO"
        onClick={() => setOpen((v) => !v)}
        className={`flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full border text-[10px] font-medium leading-none transition-colors ${
          open
            ? "border-[var(--color-brass-400)] text-[var(--color-brass-300)]"
            : "border-[var(--color-ink-500)] text-[var(--color-paper-600)] hover:border-[var(--color-brass-400)]/60 hover:text-[var(--color-brass-300)]"
        }`}
      >
        i
      </button>
      {open && (
        <div
          className="absolute right-0 top-6 z-30 w-64 rounded-lg border border-[var(--color-ink-500)] bg-[var(--color-ink-800)] p-3 text-xs leading-relaxed text-[var(--color-paper-200)] shadow-2xl shadow-black/50"
          style={{ animation: "infoPopIn 0.15s ease-out" }}
        >
          {text}
        </div>
      )}
      <style>{`
        @keyframes infoPopIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
