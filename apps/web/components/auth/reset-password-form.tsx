"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BrowserApiError, confirmPasswordReset } from "@/lib/browser-api";

import { FormField } from "./form-field";

type ResetPasswordFormProps = {
  token?: string;
};

const LINK_CLASS =
  "text-(--color-accent) underline underline-offset-4 transition-colors hover:text-(--color-accent-hover)";

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [linkError, setLinkError] = useState<string | null>(
    token ? null : "This page needs the link from your reset email.",
  );
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    // The API only receives one password, so a typo has to be caught here.
    if (password !== confirmation) {
      setFormError("The two passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await confirmPasswordReset({ token: token ?? "", password });
      setDone(true);
      // The reset signed this account out everywhere, so redraw the header.
      router.refresh();
    } catch (error) {
      if (!(error instanceof BrowserApiError)) {
        setFormError("Could not reset your password. Try again.");
      } else if (error.code?.startsWith("password_reset_token_")) {
        setLinkError(error.message);
      } else {
        setFormError(error.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="space-y-8">
        <div className="border border-(--color-border-strong) bg-[rgba(17,14,11,0.78)] px-6 py-6">
          <h3 className="font-display text-(length:--fs-heading-success) tracking-[-0.04em] text-(--color-text)">
            Password changed
          </h3>
          <p className="mt-4 font-mono text-(length:--fs-body-base) leading-7 text-(--color-accent)">
            You have been signed out everywhere. Sign in with your new password.
          </p>
        </div>
        <p className="text-center font-mono text-(length:--fs-body-base)">
          <Link href="/login" className={LINK_CLASS}>
            sign in
          </Link>
        </p>
      </div>
    );
  }

  if (linkError) {
    return (
      <div className="space-y-8">
        <p className="text-center font-mono text-(length:--fs-body-base) leading-7 text-(--color-error)">
          {linkError}
        </p>
        <p className="text-center font-mono text-(length:--fs-body-base)">
          <Link href="/forgot-password" className={LINK_CLASS}>
            request a new link
          </Link>
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <FormField
        label="New password"
        type="password"
        value={password}
        onChange={setPassword}
        placeholder="••••••••"
        hint="12+ characters"
      />
      <FormField
        label="Confirm password"
        type="password"
        value={confirmation}
        onChange={setConfirmation}
        placeholder="••••••••"
      />

      {formError ? <p className="font-mono text-xs text-(--color-error)">{formError}</p> : null}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-(--color-accent) px-6 py-2 font-mono text-sm font-bold uppercase tracking-[0.12em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
      >
        {submitting ? "saving…" : "set new password →"}
      </button>
    </form>
  );
}
