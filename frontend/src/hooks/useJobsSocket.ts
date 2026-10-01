import { useCallback, useEffect, useRef, useState } from "react";
import { jobsWebSocketUrl, listJobs } from "../lib/api";
import type { Job } from "../lib/types";

interface StatusUpdateMessage {
  job_id: string;
  status: Job["status"];
  result?: Job["result"];
  error?: string;
  // Phase 14: ephemeral live sub-stage, see status_bus.py's publish_status
  // docstring - "queued" / "ocr" / "model" / "decoding" / "done" / "failed".
  stage?: Job["stage"];
}

/**
 * Live job list - Core UX requirement #1 (project-plan.md): "Status delivery
 * via websocket (preferred) or polling fallback." Websocket se live push
 * milta hai (status_bus.py ka Redis pub/sub bridge); connection drop ho jaaye
 * to 4s polling fallback pe switch ho jaata hai - demo kabhi "stuck" nahi
 * dikhta, chahe websocket na chale.
 */
export function useJobsSocket() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const refresh = useCallback(async () => {
    try {
      const fresh = await listJobs();
      setJobs(fresh);
    } catch {
      // network blip - agla poll/refresh try karega, UI me purana data hi
      // dikhta rehta hai (crash nahi hota)
    } finally {
      setLoading(false);
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(refresh, 4000);
  }, [refresh]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const applyUpdate = useCallback((msg: StatusUpdateMessage) => {
    setJobs((prev) =>
      prev.map((job) =>
        job.id === msg.job_id
          ? {
              ...job,
              status: msg.status,
              result: msg.result ?? job.result,
              error: msg.error ?? job.error,
              // Phase 14: every publish_status call now sends a stage, but
              // fall back to whatever we already had rather than null-ing
              // it out on some future message type that omits it.
              stage: msg.stage ?? job.stage ?? null,
              updated_at: new Date().toISOString(),
            }
          : job,
      ),
    );
  }, []);

  useEffect(() => {
    void refresh();

    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(jobsWebSocketUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        stopPolling();
      };
      ws.onmessage = (event) => {
        try {
          applyUpdate(JSON.parse(event.data));
        } catch {
          // malformed frame, ignore - agla message theek hoga
        }
      };
      ws.onclose = () => {
        setConnected(false);
        startPolling();
        if (!cancelled) setTimeout(connect, 3000); // reconnect attempt
      };
      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      wsRef.current?.close();
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addJobs = useCallback((newJobs: Job[]) => {
    // Fresh rows from POST /upload are DB status "queued" with no stage push
    // yet - seed stage: "queued" so progress cards render their first dot
    // immediately instead of waiting on the first websocket message.
    setJobs((prev) => [...newJobs.map((j) => ({ ...j, stage: j.stage ?? "queued" })), ...prev]);
  }, []);

  // Local-only removal after a successful DELETE call - no websocket event
  // exists for this (deletion isn't part of the extraction pipeline), so the
  // caller updates state directly once the API call succeeds.
  const removeJob = useCallback((jobId: string) => {
    setJobs((prev) => prev.filter((job) => job.id !== jobId));
  }, []);

  // Merges a partial update (e.g. fresh review_notes from the review
  // endpoint) into one job in place - same rationale as removeJob, this is a
  // direct user action's result, not a pipeline status push.
  const patchJob = useCallback((jobId: string, patch: Partial<Job>) => {
    setJobs((prev) => prev.map((job) => (job.id === jobId ? { ...job, ...patch } : job)));
  }, []);

  return { jobs, connected, loading, addJobs, removeJob, patchJob, refresh };
}
