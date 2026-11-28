"use client";

import { useState } from "react";
import Link from "next/link";

import { BrowserApiError, requestPasswordReset } from "@/lib/browser-api";

import { FormField } from "./form-field";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      await requestPasswordReset({ email });
      setSubmitted(true);
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setFormError(error.message);
      } else {
        setFormError("Could not request a reset link. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      {submitted ? (
        <div className="border border-(--color-border-strong) bg-[rgba(17,14,11,0.78)] px-6 py-6">
          <h3 className="font-display text-(length:--fs-heading-success) tracking-[-0.04em] text-(--color-text)">
            Check your email
          </h3>
          <p className="mt-4 font-mono text-(length:--fs-body-base) leading-7 text-(--color-text-dim)">
            If that address belongs to an active account, we are sending it a reset link. The link
            works once and expires soon.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-8">
          <FormField
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="you@example.com"
          />

          {formError ? (
            <p className="font-mono text-xs text-(--color-error)">{formError}</p>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-(--color-accent) px-6 py-2 font-mono text-sm font-bold uppercase tracking-[0.12em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
          >
            {submitting ? "sending…" : "send reset link →"}
          </button>
        </form>
      )}

      <p className="text-center font-mono text-(length:--fs-body-base) text-(--color-text-dim)">
        <Link
          href="/login"
          className="text-(--color-accent) underline underline-offset-4 transition-colors hover:text-(--color-accent-hover)"
        >
          back to sign in
        </Link>
      </p>
    </div>
  );
}
