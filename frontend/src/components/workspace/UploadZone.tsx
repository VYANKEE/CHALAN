import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { uploadInvoices } from "../../lib/api";
import type { Job } from "../../lib/types";

interface Props {
  onUploaded: (jobs: Job[]) => void;
}

const ACCEPTED = [".png", ".jpg", ".jpeg"];

interface StagedFile {
  key: string;
  file: File;
  previewUrl: string;
}

function makeKey(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Stage-then-start flow. Dropping or selecting files only ADDS them to a
 * local queue - nothing is uploaded, and no backend job/Celery task exists
 * yet, until the person explicitly clicks "Start processing". One queue
 * handles both a single file and a big batch; clicking Start fires one
 * /upload call for everything staged, same backend contract as before -
 * this is purely a client-side staging change.
 */
export function UploadZone({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trayRef = useRef<HTMLDivElement>(null);
  const stagedRef = useRef<StagedFile[]>([]);
  stagedRef.current = staged;

  const addFiles = useCallback((fileList: FileList | File[]) => {
    const incoming = Array.from(fileList).filter((f) =>
      ACCEPTED.some((ext) => f.name.toLowerCase().endsWith(ext)),
    );
    if (incoming.length === 0) {
      setError("Only PNG/JPG images are supported right now.");
      return;
    }
    setError(null);
    setStaged((prev) => {
      const existingKeys = new Set(prev.map((s) => s.key));
      const additions = incoming
        .filter((f) => !existingKeys.has(makeKey(f)))
        .map((f) => ({ key: makeKey(f), file: f, previewUrl: URL.createObjectURL(f) }));
      return [...prev, ...additions];
    });
  }, []);

  const removeFile = useCallback((key: string) => {
    setStaged((prev) => {
      const target = prev.find((s) => s.key === key);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((s) => s.key !== key);
    });
  }, []);

  const clearAll = useCallback(() => {
    setStaged((prev) => {
      prev.forEach((s) => URL.revokeObjectURL(s.previewUrl));
      return [];
    });
  }, []);

  // Revoke any still-open preview URLs if this component unmounts with
  // files still staged (e.g. route change mid-queue) - avoids leaking blob
  // URLs for the life of the tab.
  useEffect(() => {
    return () => stagedRef.current.forEach((s) => URL.revokeObjectURL(s.previewUrl));
  }, []);

  useEffect(() => {
    if (trayRef.current && staged.length > 0) {
      gsap.fromTo(
        trayRef.current.children,
        { opacity: 0, y: 8 },
        { opacity: 1, y: 0, duration: 0.3, stagger: 0.04, ease: "power2.out", overwrite: "auto" },
      );
    }
  }, [staged.length]);

  const totalSize = useMemo(() => staged.reduce((sum, s) => sum + s.file.size, 0), [staged]);

  async function handleStart() {
    if (staged.length === 0 || uploading) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadInvoices(staged.map((s) => s.file));
      staged.forEach((s) => URL.revokeObjectURL(s.previewUrl));
      setStaged([]);
      onUploaded(res.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div
        data-cursor={dragging ? "DROP" : "ADD"}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`group relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed px-6 text-center transition-all duration-300 ${
          staged.length > 0 ? "py-8" : "py-16"
        } ${
          dragging
            ? "scale-[1.01] border-[var(--color-brass-400)] bg-[var(--color-brass-400)]/5"
            : "border-[var(--color-ink-500)] bg-[var(--color-ink-800)] hover:border-[var(--color-brass-500)]/60 hover:bg-[var(--color-ink-700)]"
        }`}
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
          style={{
            background: "radial-gradient(circle at 50% 0%, color-mix(in srgb, var(--color-brass-400) 10%, transparent), transparent 70%)",
          }}
        />
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <div className="relative mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-brass-400)]/10 text-[var(--color-brass-300)]">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="relative text-sm font-medium text-[var(--color-paper-50)]">
          {staged.length > 0 ? "Drop more, or click to add another" : "Drop invoices or receipts here, or click to browse"}
        </p>
        <p className="relative mt-1 text-xs text-[var(--color-paper-400)]">
          One file or a whole batch — nothing uploads until you hit Start
        </p>
      </div>

      {error && <p className="mt-2 text-sm text-[var(--color-rose-glow)]">{error}</p>}

      {staged.length > 0 && (
        <div className="mt-4 rounded-2xl border border-[var(--color-ink-600)] bg-[var(--color-ink-900)] p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-[var(--color-paper-200)]">
              {staged.length} {staged.length === 1 ? "file" : "files"} queued
              <span className="ml-2 text-xs font-normal text-[var(--color-paper-600)]">{formatBytes(totalSize)}</span>
            </p>
            <button
              type="button"
              onClick={clearAll}
              disabled={uploading}
              data-cursor="CLEAR"
              className="text-xs font-medium text-[var(--color-paper-600)] transition-colors hover:text-[var(--color-rose-glow)] disabled:opacity-50"
            >
              Clear all
            </button>
          </div>

          <div ref={trayRef} className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {staged.map((s) => (
              <div
                key={s.key}
                className="group/item relative aspect-square overflow-hidden rounded-xl border border-[var(--color-ink-600)] bg-[var(--color-ink-800)]"
              >
                <img
                  src={s.previewUrl}
                  alt={s.file.name}
                  className="h-full w-full object-cover opacity-90 transition-opacity group-hover/item:opacity-60"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[var(--color-ink-950)]/90 to-transparent px-2 pb-1.5 pt-5">
                  <p className="truncate text-[10px] font-medium text-[var(--color-paper-50)]">{s.file.name}</p>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(s.key);
                  }}
                  disabled={uploading}
                  aria-label={`Remove ${s.file.name}`}
                  data-cursor="REMOVE"
                  className="absolute right-1.5 top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-ink-950)]/80 text-[var(--color-paper-200)] opacity-0 backdrop-blur-sm transition-all hover:bg-[var(--color-rose-glow)]/90 hover:text-white group-hover/item:opacity-100 disabled:opacity-0"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleStart}
            disabled={uploading}
            data-cursor="START"
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-brass-400)] px-4 py-3 text-sm font-semibold text-[var(--color-ink-950)] transition-all hover:bg-[var(--color-brass-300)] hover:shadow-[0_0_24px_-4px_var(--color-brass-400)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? (
              <>
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--color-ink-950)]/30 border-t-[var(--color-ink-950)]" />
                Starting…
              </>
            ) : (
              <>
                Start processing {staged.length > 1 ? `${staged.length} files` : ""}
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
