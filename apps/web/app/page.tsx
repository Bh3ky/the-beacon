import { AppShell } from "@/components/layout/app-shell";
import { FeedEmptyState } from "@/components/feed/feed-empty-state";
import { FeedList } from "@/components/feed/feed-list";
import { FeedPaginationLink } from "@/components/feed/feed-pagination-link";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { StatsStrip } from "@/components/layout/stats-strip";
import { getTopFeedPage } from "@/lib/api/feeds";
import { toFeedRowViewModel } from "@/lib/feed";

async function HomeFeed({ cursor }: { cursor?: string }) {
  try {
    const feed = await getTopFeedPage(15, cursor);

    if (feed.items.length === 0) {
      return (
        <FeedEmptyState
          title="No stories yet"
          message="The feed is live, but there are no ranked posts to show yet."
        />
      );
    }

    return (
      <>
        <FeedList posts={feed.items.map(toFeedRowViewModel)} />
        {feed.page_info.next_cursor ? (
          <FeedPaginationLink
            href={`/?cursor=${encodeURIComponent(feed.page_info.next_cursor)}`}
          />
        ) : null}
      </>
    );
  } catch {
    return (
      <FeedEmptyState
        title="Feed unavailable"
        message="The frontend is wired to the real backend now. Start the API and refresh this page to load live stories."
      />
    );
  }
}

export default async function HomePage({
  searchParams,
}: {
  searchParams?: Promise<{ cursor?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  return (
    <AppShell>
      <SiteHeader activeTab="top" />

      <main className="flex-1 px-6 pb-20 pt-8 sm:px-10">
        <div className="mx-auto max-w-344">
          <section className="pb-4">
            <p className="font-mono text-(length:--fs-label) uppercase tracking-[0.32em] text-(--color-text-dim)">
              The pulse of African tech — curated by the community
            </p>
          </section>

          <StatsStrip />

          <HomeFeed cursor={resolvedSearchParams?.cursor} />
        </div>
      </main>

      <SiteFooter />
    </AppShell>
  );
}
