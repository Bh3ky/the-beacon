import { FeedPage } from "@/components/feed/feed-page";
import { getShowFeed } from "@/lib/api/feeds";

export default async function ShowPage({
  searchParams,
}: {
  searchParams?: Promise<{ cursor?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  try {
    const feed = await getShowFeed(15, resolvedSearchParams?.cursor);

    return (
      <FeedPage
        activeTab="show"
        eyebrow="Built in public"
        title="Show Rift"
        subtitle="Launches, demos, tools, and products shipped by builders across the continent."
        feed={feed}
        moreHref={
          feed.page_info.next_cursor
            ? `/show?cursor=${encodeURIComponent(feed.page_info.next_cursor)}`
            : null
        }
      />
    );
  } catch {
    return (
      <FeedPage
        activeTab="show"
        eyebrow="Built in public"
        title="Show Rift"
        subtitle="Launches, demos, tools, and products shipped by builders across the continent."
        feed={{ items: [], page_info: { next_cursor: null, has_next_page: false } }}
        moreHref={null}
      />
    );
  }
}
