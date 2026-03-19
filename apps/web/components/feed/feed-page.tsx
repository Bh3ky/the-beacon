import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import type { FeedResponse } from "@/lib/api/types";
import { toFeedRowViewModel } from "@/lib/feed";

import { FeedEmptyState } from "./feed-empty-state";
import { FeedList } from "./feed-list";
import { FeedPaginationLink } from "./feed-pagination-link";

type FeedPageProps = {
  activeTab: "top" | "new" | "ask" | "show" | "jobs";
  eyebrow: string;
  title: string;
  subtitle: string;
  feed: FeedResponse;
  moreHref: string | null;
};

export function FeedPage({
  activeTab,
  eyebrow,
  title,
  subtitle,
  feed,
  moreHref,
}: FeedPageProps) {
  return (
    <AppShell>
      <SiteHeader activeTab={activeTab} />

      <main className="flex-1 px-6 pb-20 pt-8 sm:px-10">
        <div className="mx-auto max-w-[86rem]">
          <section className="border-b border-[var(--color-border)] pb-6">
            <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.32em] text-[var(--color-text-dim)]">
              {eyebrow}
            </p>
            <h1 className="mt-5 font-display text-[length:var(--fs-heading-form)] tracking-[-0.04em] text-[var(--color-text)]">
              {title}
            </h1>
            <p className="mt-3 max-w-3xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
              {subtitle}
            </p>
          </section>

          <section className="pt-2">
            {feed.items.length > 0 ? (
              <FeedList posts={feed.items.map(toFeedRowViewModel)} />
            ) : (
              <FeedEmptyState
                title="No stories here yet"
                message="This feed is live, but there is nothing to show in this slice right now."
              />
            )}
          </section>

          {moreHref ? (
            <FeedPaginationLink href={moreHref} />
          ) : null}
        </div>
      </main>

      <SiteFooter />
    </AppShell>
  );
}
