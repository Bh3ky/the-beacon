import { FeedPage } from "@/components/feed/feed-page";
import { getJobsFeed } from "@/lib/api/feeds";

export default async function JobsPage({
  searchParams,
}: {
  searchParams?: Promise<{ cursor?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  const feed = await getJobsFeed(15, resolvedSearchParams?.cursor);

  return (
    <FeedPage
      activeTab="jobs"
      eyebrow="Roles and opportunities"
      title="Jobs"
      subtitle="A dedicated jobs feed for African tech teams hiring across the continent and globally."
      feed={feed}
      moreHref={
        feed.page_info.next_cursor
          ? `/jobs?cursor=${encodeURIComponent(feed.page_info.next_cursor)}`
          : null
      }
    />
  );
}
