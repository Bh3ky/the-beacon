import Link from "next/link";

import { CategoryBadge, type FeedCategory } from "./category-badge";

export type FeedRowModel = {
  id: number;
  title: string;
  domain: string | null;
  points: number;
  author: string;
  time: string;
  comments: number;
  category: FeedCategory;
};

export function FeedRow({ post, rank }: { post: FeedRowModel; rank: number }) {
  return (
    <article className="group grid grid-cols-[2rem_2.5rem_1fr] gap-4 border-b border-[var(--color-border)] py-5 transition-colors hover:bg-[var(--color-surface-hover)]">
      <span className="pt-1 text-right font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        {rank}.
      </span>

      <div className="flex flex-col items-center gap-1.5 pt-0.5">
        <button
          type="button"
          aria-label={`Upvote ${post.title}`}
          className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-accent)]"
        >
          ▲
        </button>
        <span className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-muted)]">
          {post.points}
        </span>
      </div>

      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-2">
          <CategoryBadge category={post.category} />
          <Link
            href={`/post/demo-${post.id}/placeholder-slug`}
            className="font-display text-[length:var(--fs-body-feed-title)] leading-[1.35] tracking-[-0.02em] text-[var(--color-text)] transition-colors hover:text-[var(--color-accent)]"
          >
            {post.title}
          </Link>
          {post.domain ? (
            <span className="font-mono text-[length:var(--fs-label)] text-[var(--color-text-dim)]">
              ({post.domain})
            </span>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
          <span>
            by{" "}
            <span className="text-[var(--color-text-muted)]">{post.author}</span>
          </span>
          <span>{post.time}</span>
          <Link
            href={`/post/demo-${post.id}/placeholder-slug`}
            className="transition-colors hover:text-[var(--color-accent)]"
          >
            {post.comments} comments
          </Link>
          <button
            type="button"
            className="transition-colors hover:text-[var(--color-accent)]"
          >
            hide
          </button>
        </div>
      </div>
    </article>
  );
}
