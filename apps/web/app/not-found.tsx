import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

export default function NotFound() {
  return (
    <AppShell>
      <SiteHeader activeTab={null} />

      <main className="flex-1 px-6 pb-20 pt-16 sm:px-10">
        <div className="mx-auto max-w-3xl">
          <p className="font-mono text-(length:--fs-label) uppercase tracking-[0.32em] text-(--color-text-dim)">
            404
          </p>
          <h1 className="mt-5 font-display text-(length:--fs-heading-form) tracking-[-0.04em] text-(--color-text)">
            We couldn&apos;t find that page.
          </h1>
          <p className="mt-3 font-mono text-(length:--fs-body-base) leading-7 text-(--color-text-dim)">
            The link may be broken, or the post may have been removed.
          </p>
          <Link
            href="/"
            className="mt-8 inline-block bg-(--color-accent) px-6 py-4 font-mono text-(length:--fs-body-base) font-bold uppercase tracking-widest text-(--color-nav-text-on-accent) transition-colors hover:bg-(--color-accent-hover)"
          >
            back to the feed
          </Link>
        </div>
      </main>

      <SiteFooter />
    </AppShell>
  );
}
