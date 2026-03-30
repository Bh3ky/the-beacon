"use client";

import { useState } from "react";

import type { FlagQueueItemPayload, UserPayload } from "@/lib/api/types";
import {
  BrowserApiError,
  banModeratedUser,
  dismissFlag,
  removeModeratedComment,
  removeModeratedPost,
  suspendModeratedUser,
} from "@/lib/browser-api";

type ModerationDashboardProps = {
  initialItems: FlagQueueItemPayload[];
  currentUser: UserPayload;
};

type ActionKind = "dismiss" | "remove_post" | "remove_comment" | "suspend_user" | "ban_user";

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function ModerationDashboard({
  initialItems,
  currentUser,
}: ModerationDashboardProps) {
  const [items, setItems] = useState(initialItems);
  const [reasonByFlagId, setReasonByFlagId] = useState<Record<string, string>>({});
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleAction(item: FlagQueueItemPayload, action: ActionKind) {
    const requestKey = `${item.flag.id}:${action}`;
    setPendingAction(requestKey);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const reason = reasonByFlagId[item.flag.id]?.trim() || null;

      if (action === "dismiss") {
        await dismissFlag(item.flag.id);
      } else if (action === "remove_post") {
        await removeModeratedPost(item.target.id, { reason, flag_id: item.flag.id });
      } else if (action === "remove_comment") {
        await removeModeratedComment(item.target.id, { reason, flag_id: item.flag.id });
      } else if (action === "suspend_user") {
        await suspendModeratedUser(item.target.id, { reason, flag_id: item.flag.id });
      } else {
        await banModeratedUser(item.target.id, { reason, flag_id: item.flag.id });
      }

      setItems((current) => current.filter((entry) => entry.flag.id !== item.flag.id));
      setReasonByFlagId((current) => {
        const next = { ...current };
        delete next[item.flag.id];
        return next;
      });
      setSuccessMessage("Queue updated.");
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Could not complete the moderation action.");
      }
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="pt-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.32em] text-[var(--color-text-dim)]">
            moderation queue
          </p>
          <h1 className="mt-5 font-display text-[length:var(--fs-heading-form)] tracking-[-0.04em] text-[var(--color-text)]">
            Open reports
          </h1>
          <p className="mt-3 max-w-3xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
            Review community flags, apply lightweight enforcement, and keep every action auditable.
          </p>
        </div>
        <div className="rounded-sm border border-[var(--color-border)] px-4 py-3 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
          signed in as {currentUser.role}
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
            Queue clear
          </p>
          <p className="mt-3 max-w-2xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
            There are no open reports waiting for review right now.
          </p>
        </div>
      ) : (
        <div className="mt-8 space-y-8">
          {items.map((item) => {
            const reasonValue = reasonByFlagId[item.flag.id] ?? "";
            const isBusy = pendingAction !== null && pendingAction.startsWith(`${item.flag.id}:`);

            return (
              <article
                key={item.flag.id}
                className="border border-[var(--color-border)] bg-[rgba(13,11,8,0.18)] px-7 py-7"
              >
                <div className="flex flex-wrap items-center gap-x-5 gap-y-3 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em] text-[var(--color-text-dim)]">
                  <span>{item.flag.target_type}</span>
                  <span>{item.flag.reason_code.replace("_", " ")}</span>
                  <span>{formatTimestamp(item.flag.created_at)}</span>
                  <span>reported by {item.reporter.username}</span>
                  <span className="text-[var(--color-accent)]">{item.target.status}</span>
                </div>

                <div className="mt-5">
                  <h2 className="font-display text-[length:var(--fs-heading-success)] tracking-[-0.03em] text-[var(--color-text)]">
                    {item.target.title ?? item.target.username ?? "Flagged content"}
                  </h2>
                  {item.target.username && item.target.target_type !== "user" ? (
                    <p className="mt-2 font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
                      author: {item.target.username}
                    </p>
                  ) : null}
                  {item.target.excerpt ? (
                    <p className="mt-4 whitespace-pre-wrap font-display text-[length:var(--fs-body-comment)] leading-[1.8] text-[var(--color-text)]">
                      {item.target.excerpt}
                    </p>
                  ) : null}
                  {item.flag.notes ? (
                    <div className="mt-5 border-l-2 border-[var(--color-accent)] pl-4">
                      <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
                        reporter notes
                      </p>
                      <p className="mt-2 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text)]">
                        {item.flag.notes}
                      </p>
                    </div>
                  ) : null}
                </div>

                <label className="mt-6 block">
                  <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
                    moderator reason
                  </span>
                  <textarea
                    value={reasonValue}
                    onChange={(event) =>
                      setReasonByFlagId((current) => ({
                        ...current,
                        [item.flag.id]: event.target.value,
                      }))
                    }
                    rows={3}
                    placeholder="brief internal reason for the action"
                    className="mt-2 w-full resize-y border border-[var(--color-border)] bg-transparent px-3 py-3 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text)] outline-none transition-colors placeholder:text-[var(--color-text-faint)] focus:border-[var(--color-accent)]"
                  />
                </label>

                <div className="mt-6 flex flex-wrap gap-4 font-mono text-[length:var(--fs-meta)] uppercase tracking-[0.14em]">
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handleAction(item, "dismiss")}
                    className="border border-[var(--color-border)] px-4 py-3 text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-text)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                  >
                    {pendingAction === `${item.flag.id}:dismiss` ? "dismissing…" : "dismiss"}
                  </button>

                  {item.target.target_type === "post" ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => void handleAction(item, "remove_post")}
                      className="border border-[rgba(184,63,32,0.45)] px-4 py-3 text-[var(--color-error)] transition-colors hover:border-[var(--color-error)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                    >
                      {pendingAction === `${item.flag.id}:remove_post` ? "removing…" : "remove post"}
                    </button>
                  ) : null}

                  {item.target.target_type === "comment" ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => void handleAction(item, "remove_comment")}
                      className="border border-[rgba(184,63,32,0.45)] px-4 py-3 text-[var(--color-error)] transition-colors hover:border-[var(--color-error)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                    >
                      {pendingAction === `${item.flag.id}:remove_comment` ? "removing…" : "remove comment"}
                    </button>
                  ) : null}

                  {item.target.target_type === "user" ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => void handleAction(item, "suspend_user")}
                      className="border border-[rgba(184,63,32,0.45)] px-4 py-3 text-[var(--color-error)] transition-colors hover:border-[var(--color-error)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                    >
                      {pendingAction === `${item.flag.id}:suspend_user` ? "suspending…" : "suspend user"}
                    </button>
                  ) : null}

                  {item.target.target_type === "user" && currentUser.role === "admin" ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => void handleAction(item, "ban_user")}
                      className="border border-[rgba(184,63,32,0.7)] bg-[rgba(184,63,32,0.08)] px-4 py-3 text-[var(--color-error)] transition-colors hover:border-[var(--color-error)] disabled:cursor-wait disabled:text-[var(--color-text-faint)]"
                    >
                      {pendingAction === `${item.flag.id}:ban_user` ? "banning…" : "ban user"}
                    </button>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
