"use client";

import { useEffect } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <AppShell>
      <SiteHeader activeTab={null} />

      <main className="flex-1 px-6 pb-20 pt-16 sm:px-10">
        <div className="mx-auto max-w-3xl">
          <p className="font-mono text-(length:--fs-label) uppercase tracking-[0.32em] text-(--color-text-dim)">
            Something went wrong
          </p>
          <h1 className="mt-5 font-display text-(length:--fs-heading-form) tracking-[-0.04em] text-(--color-text)">
            We couldn&apos;t load this page.
          </h1>
          <p className="mt-3 font-mono text-(length:--fs-body-base) leading-7 text-(--color-text-dim)">
            This is on us. Try again in a moment.
          </p>
          {error.digest ? (
            <p className="mt-3 font-mono text-(length:--fs-meta) text-(--color-text-faint)">
              Reference: {error.digest}
            </p>
          ) : null}
          <button
            type="button"
            onClick={reset}
            className="mt-8 bg-(--color-accent) px-6 py-4 font-mono text-(length:--fs-body-base) font-bold uppercase tracking-widest text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover)"
          >
            try again
          </button>
        </div>
      </main>

      <SiteFooter />
    </AppShell>
  );
}
