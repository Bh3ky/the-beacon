"use client";

import { useState } from "react";

import { BrowserApiError, createFlag } from "@/lib/browser-api";

const FLAG_REASONS = [
  { value: "spam", label: "spam" },
  { value: "abuse", label: "abuse" },
  { value: "misinformation", label: "misinformation" },
  { value: "off_topic", label: "off-topic" },
  { value: "other", label: "other" },
] as const;

type FlagActionProps = {
  targetType: "post" | "comment" | "user";
  targetId: string;
  subjectLabel: string;
};

export function FlagAction({ targetType, targetId, subjectLabel }: FlagActionProps) {
  const [showFlagForm, setShowFlagForm] = useState(false);
  const [reasonCode, setReasonCode] =
    useState<(typeof FLAG_REASONS)[number]["value"]>("spam");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await createFlag({
        target_type: targetType,
        target_id: targetId,
        reason_code: reasonCode,
        notes,
      });
      setSuccessMessage(`${subjectLabel} reported`);
      setShowFlagForm(false);
      setNotes("");
    } catch (error) {
      if (error instanceof BrowserApiError) {
        if (error.status === 401) {
          setErrorMessage(`sign in to report this ${subjectLabel}`);
        } else if (error.code === "duplicate_open_flag") {
          setErrorMessage("you already reported this reason");
        } else {
          setErrorMessage(error.message.toLowerCase());
        }
      } else {
        setErrorMessage("could not submit report");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          setShowFlagForm((current) => !current);
          setErrorMessage(null);
          setSuccessMessage(null);
        }}
        className="transition-colors hover:text-[var(--color-accent)]"
      >
        flag
      </button>

      {successMessage ? (
        <p className="mt-3 font-mono text-[length:var(--fs-meta)] text-[var(--color-accent)]">
          {successMessage}
        </p>
      ) : null}

      {showFlagForm ? (
        <form onSubmit={handleSubmit} className="mt-4 space-y-4 border-t border-[var(--color-border)] pt-4">
          <label className="block">
            <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
              reason
            </span>
            <select
              value={reasonCode}
              onChange={(event) => setReasonCode(event.target.value as typeof reasonCode)}
              className="mt-2 w-full border border-[var(--color-border)] bg-[rgba(13,11,8,0.7)] px-3 py-3 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text)] outline-none transition-colors focus:border-[var(--color-accent)]"
            >
              {FLAG_REASONS.map((reason) => (
                <option key={reason.value} value={reason.value}>
                  {reason.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
              notes
            </span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              placeholder="add context if needed"
              className="mt-2 w-full resize-y border border-[var(--color-border)] bg-transparent px-3 py-3 font-display text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text)] outline-none transition-colors placeholder:text-[var(--color-text-faint)] focus:border-[var(--color-accent)]"
            />
          </label>

          {errorMessage ? (
            <p className="font-mono text-[length:var(--fs-meta)] text-[var(--color-error)]">
              {errorMessage}
            </p>
          ) : null}

          <div className="flex items-center gap-4 font-mono text-[length:var(--fs-meta)]">
            <button
              type="submit"
              disabled={submitting}
              className="text-[var(--color-accent)] transition-colors hover:text-[var(--color-accent-hover)] disabled:cursor-wait disabled:text-[var(--color-text-dim)]"
            >
              {submitting ? "sending…" : "submit report"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowFlagForm(false);
                setErrorMessage(null);
              }}
              className="text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-text)]"
            >
              cancel
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
