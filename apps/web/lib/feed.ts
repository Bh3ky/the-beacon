import type { FeedCategory } from "@/components/feed/category-badge";
import type { PostPayload } from "@/lib/api/types";

export type FeedRowViewModel = {
  id: string;
  slug: string;
  title: string;
  url: string | null;
  domain: string | null;
  points: number;
  viewerVote: 1 | -1 | null;
  author: string;
  time: string;
  comments: number;
  category: FeedCategory;
};

function normalizeCategory(category: string): FeedCategory {
  switch (category) {
    case "funding":
    case "show":
    case "ask":
    case "opinion":
    case "policy":
    case "ecosystem":
    case "engineering":
    case "launch":
    case "job":
    case "jobs":
    case "news":
      return category === "jobs" ? "job" : category;
    default:
      return "news";
  }
}

export function formatRelativeTime(value: string): string {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return "just now";
  }

  const diffMs = Date.now() - timestamp.getTime();
  const diffMinutes = Math.max(0, Math.floor(diffMs / 60_000));

  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
}

export function formatCompactCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function toFeedRowViewModel(post: PostPayload): FeedRowViewModel {
  return {
    id: post.id,
    slug: post.slug,
    title: post.title,
    url: post.url,
    domain: post.domain?.hostname ?? null,
    points: post.score,
    viewerVote: post.viewer_vote as 1 | -1 | null,
    author: post.author.username,
    time: formatRelativeTime(post.submitted_at),
    comments: post.comment_count,
    category: normalizeCategory(post.category),
  };
}
