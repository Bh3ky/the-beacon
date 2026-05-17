"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BrowserApiError, login, resendVerification } from "@/lib/browser-api";

import { FormField } from "./form-field";

type LoginFormProps = {
  nextHref?: string;
  registeredEmail?: string;
};

export function LoginForm({ nextHref, registeredEmail }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState(registeredEmail ?? "");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [resentNotice, setResentNotice] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setResentNotice(null);
    setSubmitting(true);

    try {
      await login({ email, password });
      router.push(nextHref || "/");
      router.refresh();
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setFormError(error.message);
        return;
      }
      setFormError("Sign in failed. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setFormError(null);
    setResentNotice(null);
    setResending(true);

    try {
      await resendVerification({ email });
      setResentNotice("A fresh verification link is on its way.");
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setFormError(error.message);
      } else {
        setFormError("Could not resend the verification link.");
      }
    } finally {
      setResending(false);
    }
  }

  const showResend = formError !== null && formError.toLowerCase().includes("pending verification");

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-8">
        <FormField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
        />
        <FormField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="••••••••"
        />

        {formError ? (
          <p className="font-mono text-xs text-(--color-error)">
            {formError}
          </p>
        ) : null}

        {resentNotice ? (
          <p className="font-mono text-xs text-(--color-accent)">
            {resentNotice}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-(--color-accent) px-6 py-2 font-mono text-sm font-bold uppercase tracking-[0.12em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
        >
          {submitting ? "signing in…" : "sign in →"}
        </button>
      </form>

      {showResend ? (
        <div className="mt-6 flex items-center justify-between gap-4 border border-(--color-border) px-4 py-4">
          <p className="font-mono text-(length:--fs-meta) leading-6 text-(--color-text-dim)">
            This account still needs verification before it can sign in.
          </p>
          <button
            type="button"
            onClick={handleResend}
            disabled={resending}
            className="shrink-0 font-mono text-(length:--fs-body-base) text-(--color-accent) underline-offset-4 transition-colors hover:text-(--color-accent-hover) hover:underline disabled:cursor-wait disabled:text-(--color-text-dim)"
          >
            {resending ? "sending…" : "resend link"}
          </button>
        </div>
      ) : null}

      <p className="mt-8 text-center font-mono text-(length:--fs-body-base) text-(--color-text-dim)">
        New here?{" "}
        <Link
          href="/register"
          className="text-(--color-accent) underline underline-offset-4 transition-colors hover:text-(--color-accent-hover)"
        >
          create an account
        </Link>
      </p>
    </div>
  );
}
