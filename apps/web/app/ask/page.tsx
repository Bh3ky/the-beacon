import { FeedPage } from "@/components/feed/feed-page";
import { getAskFeed } from "@/lib/api/feeds";

export default async function AskPage({
  searchParams,
}: {
  searchParams?: Promise<{ cursor?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  const feed = await getAskFeed(15, resolvedSearchParams?.cursor);

  return (
    <FeedPage
      activeTab="ask"
      eyebrow="Questions from builders"
      title="Ask Rift"
      subtitle="Open questions, operator dilemmas, and practical requests for insight from the African tech community."
      feed={feed}
      moreHref={
        feed.page_info.next_cursor
          ? `/ask?cursor=${encodeURIComponent(feed.page_info.next_cursor)}`
          : null
      }
    />
  );
}
