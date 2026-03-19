import Link from "next/link";

import { VoteControl } from "@/components/vote/vote-control";

import { CategoryBadge, type FeedCategory } from "./category-badge";

export type FeedRowModel = {
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

export function FeedRow({ post, rank }: { post: FeedRowModel; rank: number }) {
  const discussionHref = `/post/${post.id}/${post.slug}`;
  const titleHref = post.url ?? discussionHref;

  return (
    <article className="group grid grid-cols-[2rem_1fr] gap-4 border-b border-[var(--color-border)] py-5 transition-colors hover:bg-[var(--color-surface-hover)]">
      <span className="pt-1 text-right font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        {rank}.
      </span>

      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-2">
          <VoteControl
            target="post"
            targetId={post.id}
            initialScore={post.points}
            initialViewerVote={post.viewerVote}
            orientation="horizontal"
            compact
          />
          <CategoryBadge category={post.category} />
          <a
            href={titleHref}
            target={post.url ? "_blank" : undefined}
            rel={post.url ? "noreferrer" : undefined}
            className="feed-row-title-link font-display text-[length:var(--fs-body-feed-title)] leading-[1.35] tracking-[-0.02em] text-[var(--color-text)] transition-colors"
          >
            {post.title}
          </a>
          {post.domain ? (
            <a
              href={titleHref}
              target={post.url ? "_blank" : undefined}
              rel={post.url ? "noreferrer" : undefined}
              className="feed-row-domain-link font-mono text-[length:var(--fs-label)] text-[var(--color-text-dim)] transition-colors"
            >
              ({post.domain})
            </a>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
          <span>
            by{" "}
            <span className="text-[var(--color-text-muted)]">{post.author}</span>
          </span>
          <span>{post.time}</span>
          <Link
            href={discussionHref}
            className="feed-row-comments-link text-[var(--color-text-dim)] transition-colors"
          >
            {post.comments} comments
          </Link>
          <button
            type="button"
            className="feed-row-hide-button transition-colors"
          >
            hide
          </button>
        </div>
      </div>
    </article>
  );
}
