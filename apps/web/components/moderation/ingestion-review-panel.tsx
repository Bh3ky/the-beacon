"use client";

import { useState } from "react";

import type {
  IngestionReviewItemPayload,
  SourceHealthPayload,
  UserPayload,
} from "@/lib/api/types";
import {
  approveIngestionItem,
  BrowserApiError,
  rejectIngestionItem,
} from "@/lib/browser-api";

type IngestionReviewPanelProps = {
  initialItems: IngestionReviewItemPayload[];
  initialSourceHealth: SourceHealthPayload[];
  currentUser: UserPayload;
};

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "never";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function IngestionReviewPanel({
  initialItems,
  initialSourceHealth,
  currentUser,
}: IngestionReviewPanelProps) {
  const [items, setItems] = useState(initialItems);
  const [reasonByItemId, setReasonByItemId] = useState<Record<string, string>>({});
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const canReview = currentUser.role === "admin";

  async function handleAction(item: IngestionReviewItemPayload, action: "approve" | "reject") {
    const requestKey = `${item.id}:${action}`;
    setPendingAction(requestKey);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const reason = reasonByItemId[item.id]?.trim() || null;
      if (action === "approve") {
        await approveIngestionItem(item.id, { reason });
      } else {
        await rejectIngestionItem(item.id, { reason });
      }
      setItems((current) => current.filter((entry) => entry.id !== item.id));
      setReasonByItemId((current) => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
      setSuccessMessage("Ingestion queue updated.");
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Could not complete the ingestion review action.");
      }
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="pt-16">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.32em] text-[var(--color-text-dim)]">
            ingestion review
          </p>
          <h2 className="mt-5 font-display text-[length:var(--fs-heading-form)] tracking-[-0.04em] text-[var(--color-text)]">
            Awaiting review
          </h2>
          <p className="mt-3 max-w-3xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
            Approve trusted staged stories into the main feed or reject weak imports before they become posts.
          </p>
        </div>
      </div>

      {successMessage ? (
        <p className="mt-5 font-mono text-[length:var(--fs-meta)] text-[var(--color-accent)]">
          {successMessage}
        </p>
      ) : null}
      {errorMessage ? (
        <p className="mt-5 font-mono text-[length:var(--fs-meta)] text-[var(--color-error)]">
          {errorMessage}
        </p>
      ) : null}

      {items.length === 0 ? (
        <div className="mt-8 border border-[var(--color-border)] bg-[rgba(13,11,8,0.16)] px-8 py-10">
          <p className="font-display text-[length:var(--fs-heading-success)] tracking-[-0.03em] text-[var(--color-text)]">
            Review queue clear
          </p>
          <p className="mt-3 max-w-2xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
            There are no staged ingestion items waiting for manual review right now.
          </p>
        </div>
      ) : (
        <div className="mt-8 space-y-8">
          {items.map((item) => {
            const reasonValue = reasonByItemId[item.id] ?? "";
            const isBusy = pendingAction !== null && pendingAction.startsWith(`${item.id}:`);

            return (
              <article
                key={item.id}
                className="border border-[var(--color-border)] bg-[rgba(13,11,8,0.18)] px-7 py-7"
              >
                <div className="flex flex-wrap items-center gap-x-5 gap-y-3 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em] text-[var(--color-text-dim)]">
                  <span>{item.source.name}</span>
                  <span>{item.source.source_type}</span>
                  <span>{item.detected_category ?? "uncategorized"}</span>
                  <span>{formatTimestamp(item.discovered_at)}</span>
                  <span className="text-[var(--color-accent)]">{item.ingestion_status}</span>
                </div>

                <div className="mt-5">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-display text-[length:var(--fs-heading-success)] tracking-[-0.03em] text-[var(--color-text)] underline-offset-4 hover:underline"
                  >
                    {item.title}
                  </a>
                  {item.processing_notes ? (
                    <p className="mt-4 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
                      {item.processing_notes}
                    </p>
                  ) : null}
                </div>

                {canReview ? (
                  <>
                    <label className="mt-6 block">
                      <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
                        review reason
                      </span>
                      <textarea
                        value={reasonValue}
                        onChange={(event) =>
                          setReasonByItemId((current) => ({
                            ...current,
                            [item.id]: event.target.value,
                          }))
                        }
                        rows={3}
                        placeholder="brief note for the review log"
                        className="mt-2 w-full resize-y border border-[var(--color-border)] bg-transparent px-3 py-3 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text)] outline-none transition-colors placeholder:text-[var(--color-text-faint)] focus:border-[var(--color-accent)]"
                      />
                    </label>

                    <div className="mt-6 flex flex-wrap gap-4 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em]">
                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => void handleAction(item, "approve")}
                        className="border border-[var(--color-accent)] bg-[rgba(163,127,80,0.08)] px-4 py-3 text-[var(--color-accent)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                      >
                        {pendingAction === `${item.id}:approve` ? "approving…" : "approve"}
                      </button>
                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => void handleAction(item, "reject")}
                        className="border border-[rgba(184,63,32,0.45)] px-4 py-3 text-[var(--color-error)] transition-colors hover:border-[var(--color-error)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                      >
                        {pendingAction === `${item.id}:reject` ? "rejecting…" : "reject"}
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="mt-6 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em] text-[var(--color-text-dim)]">
                    Read-only for moderators. Approval and rejection require admin access.
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}

      <div className="mt-14 border-t border-[var(--color-border)] pt-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.24em] text-[var(--color-text-dim)]">
              source health
            </p>
            <h3 className="mt-4 font-display text-[length:var(--fs-heading-success)] tracking-[-0.03em] text-[var(--color-text)]">
              Recent source failures
            </h3>
          </div>
        </div>

        {initialSourceHealth.length === 0 ? (
          <p className="mt-5 font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
            No active source failures are visible right now.
          </p>
        ) : (
          <div className="mt-6 space-y-4">
            {initialSourceHealth.map((source) => (
              <article
                key={source.id}
                className="border border-[var(--color-border)] bg-[rgba(13,11,8,0.14)] px-5 py-5"
              >
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em] text-[var(--color-text-dim)]">
                  <span>{source.name}</span>
                  <span>{source.source_type}</span>
                  <span>poll {source.poll_interval_minutes}m</span>
                  <span>{source.auto_publish ? "auto publish" : "review first"}</span>
                  <span className="text-[var(--color-error)]">{formatTimestamp(source.last_error_at)}</span>
                </div>
                <p className="mt-3 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text)]">
                  {source.last_error_message ?? "Unknown source failure."}
                </p>
                <p className="mt-2 font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
                  last success: {formatTimestamp(source.last_success_at)}
                </p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
