"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BrowserApiError, verifyAccount } from "@/lib/browser-api";

import { FormField } from "./form-field";

type VerifyFormProps = {
  initialToken?: string;
  nextHref?: string;
};

type VerifyState = "idle" | "verifying" | "success" | "error";

export function VerifyForm({ initialToken, nextHref }: VerifyFormProps) {
  const router = useRouter();
  const [token, setToken] = useState(initialToken ?? "");
  const [state, setState] = useState<VerifyState>(initialToken ? "verifying" : "idle");
  const [message, setMessage] = useState<string | null>(
    initialToken ? "Verifying your account…" : null,
  );
  const attemptedAutoVerify = useRef(false);

  async function runVerification(targetToken: string) {
    setState("verifying");
    setMessage("Verifying your account…");

    try {
      await verifyAccount({ token: targetToken });
      setState("success");
      setMessage("Your account is verified and your session is live.");
      router.push(nextHref || "/");
      router.refresh();
    } catch (error) {
      setState("error");
      if (error instanceof BrowserApiError) {
        setMessage(error.message);
      } else {
        setMessage("Verification failed. Try again.");
      }
    }
  }

  useEffect(() => {
    if (!initialToken || attemptedAutoVerify.current) {
      return;
    }
    attemptedAutoVerify.current = true;
    void runVerification(initialToken);
  }, [initialToken]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runVerification(token);
  }

  return (
    <div className="space-y-8">
      <div className="border border-(--color-border-strong) bg-[rgba(17,14,11,0.78)] px-6 py-6">
        <h3 className="font-display text-(length:--fs-heading-success) tracking-[-0.04em] text-(--color-text)">
          {state === "success" ? "You&apos;re verified" : "Verify your account"}
        </h3>
        <p
          className={[
            "mt-4 font-mono text-(length:--fs-body-base) leading-7",
            state === "error"
              ? "text-(--color-error)"
              : state === "success"
                ? "text-(--color-accent)"
                : "text-(--color-text-dim)",
          ].join(" ")}
        >
          {message ??
            "Paste the token from your verification link or open this page from the email directly."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <FormField
          label="Verification token"
          value={token}
          onChange={setToken}
          placeholder="paste your token here"
        />

        <button
          type="submit"
          disabled={state === "verifying"}
          className="w-full bg-(--color-accent) px-6 py-5 font-mono text-(length:--fs-body-base) font-bold uppercase tracking-[0.14em] text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover) disabled:cursor-wait disabled:bg-(--color-accent-dim)"
        >
          {state === "verifying" ? "verifying…" : "verify account →"}
        </button>
      </form>

      <div className="flex flex-wrap gap-6 font-mono text-(length:--fs-body-base) text-(--color-text-dim)">
        <Link
          href="/login"
          className="text-(--color-accent) underline underline-offset-4 transition-colors hover:text-(--color-accent-hover)"
        >
          back to sign in
        </Link>
        <Link
          href="/register"
          className="text-(--color-text-dim) transition-colors hover:text-(--color-accent)"
        >
          need a new account?
        </Link>
      </div>
    </div>
  );
}
