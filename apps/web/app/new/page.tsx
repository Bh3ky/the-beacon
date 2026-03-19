import { FeedPage } from "@/components/feed/feed-page";
import { getNewFeed } from "@/lib/api/feeds";

export default async function NewPage({
  searchParams,
}: {
  searchParams?: Promise<{ cursor?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  try {
    const feed = await getNewFeed(15, resolvedSearchParams?.cursor);

    return (
      <FeedPage
        activeTab="new"
        eyebrow="Fresh from the network"
        title="Newest posts"
        subtitle="Chronological signal from builders, operators, founders, and analysts across the African tech ecosystem."
        feed={feed}
        moreHref={
          feed.page_info.next_cursor
            ? `/new?cursor=${encodeURIComponent(feed.page_info.next_cursor)}`
            : null
        }
      />
    );
  } catch {
    return (
      <FeedPage
        activeTab="new"
        eyebrow="Fresh from the network"
        title="Newest posts"
        subtitle="Chronological signal from builders, operators, founders, and analysts across the African tech ecosystem."
        feed={{ items: [], page_info: { next_cursor: null, has_next_page: false } }}
        moreHref={null}
      />
    );
  }
}
