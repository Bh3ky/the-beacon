"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { BrowserApiError, register, resendVerification } from "@/lib/browser-api";

import { FormField } from "./form-field";

type FieldErrors = {
  username?: string;
  email?: string;
  password?: string;
};

export function RegisterForm() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successEmail, setSuccessEmail] = useState<string | null>(null);
  const [resentNotice, setResentNotice] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const trimmedEmail = useMemo(() => email.trim(), [email]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    setResentNotice(null);
    setFieldErrors({});

    try {
      await register({ username, email, password });
      setSuccessEmail(trimmedEmail);
    } catch (error) {
      if (error instanceof BrowserApiError) {
        if (error.code === "duplicate_username") {
          setFieldErrors({ username: error.message });
        } else if (error.code === "duplicate_email") {
          setFieldErrors({ email: error.message });
        } else if (error.code === "validation_error") {
          setFormError(error.message);
        } else {
          setFormError(error.message);
        }
      } else {
        setFormError("Registration failed. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    const targetEmail = successEmail ?? trimmedEmail;
    if (!targetEmail) {
      setFormError("Enter the account email first.");
      return;
    }

    setResending(true);
    setFormError(null);
    setResentNotice(null);

    try {
      await resendVerification({ email: targetEmail });
      setResentNotice("Verification link resent.");
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

  if (successEmail) {
    return (
      <div className="space-y-8">
        <div className="border border-(--color-border-strong) bg-[rgba(17,14,11,0.78)] px-6 py-6">
          <h3 className="font-display text-(length:--fs-heading-success) tracking-[-0.04em] text-(--color-text)">
            Check your email!
          </h3>
          <p className="mt-4 font-mono text-(length:--fs-body-base) leading-7 text-(--color-text-dim)">
            We've sent you a verification link to{" "}
            <span className="text-(--color-text)">{successEmail}</span>
            , please click it too verify your email adress. 
          </p>
        </div>

        {formError ? (
          <p className="font-mono text-(length:--fs-body-base) text-(--color-error)">
            {formError}
          </p>
        ) : null}

        {resentNotice ? (
          <p className="font-mono text-(length:--fs-body-base) text-(--color-accent)">
            {resentNotice}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-4">
          <button
            type="button"
            onClick={handleResend}
            disabled={resending}
            className="bg-(--color-accent) px-6 py-4 font-mono text-(length:--fs-body-base) font-bold uppercase tracking-[0.12em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
          >
            {resending ? "sending…" : "resend link"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-8">
        <FormField
          label="Username"
          value={username}
          onChange={setUsername}
          placeholder="username"
          error={fieldErrors.username ?? null}
        />
        <FormField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
          error={fieldErrors.email ?? null}
        />
        <FormField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="••••••••"
          hint="8+ characters recommended"
        />

        {formError ? (
          <p className="font-mono text-(length:--fs-body-base) text-(--color-error)">
            {formError}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-(--color-accent) px-6 py-5 font-mono text-(length:--fs-body-base) font-bold uppercase tracking-[0.14em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
        >
          {submitting ? "creating…" : "join rifthub →"}
        </button>
      </form>

      <p className="mt-8 text-center font-mono text-(length:--fs-body-base) text-(--color-text-dim)">
        Already a member?{" "}
        <Link
          href="/login"
          className="text-(--color-accent) underline underline-offset-4 transition-colors hover:text-(--color-accent-hover)"
        >
          sign in
        </Link>
      </p>
      <p className="font-mono text-(length:--fs-meta) text-center leading-6 text-(--color-text-dim)">
          By joining you agree to the community guidelines.
      </p>
    </div>
  );
}
