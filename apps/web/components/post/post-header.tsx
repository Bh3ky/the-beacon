import Image from "next/image";
import Link from "next/link";
import logoImage from "../../../../public/rifthub-logo.png";

import { VoteControl } from "@/components/vote/vote-control";
import type { PostPayload } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/feed";

export function PostHeader({ post }: { post: PostPayload }) {
  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-accent)] px-6 py-5 sm:px-10">
      <div className="mx-auto flex max-w-[86rem] items-center justify-between gap-6">
        <div className="flex min-w-0 items-center gap-4">
          <Link href="/" className="flex items-center gap-4">
            <div className="h-12 w-12 overflow-hidden rounded-md bg-[var(--color-nav-text-on-accent)]">
              <Image
                src={logoImage}
                alt="RiftHub logo"
                width={48}
                height={48}
                className="h-full w-full object-cover"
                priority
              />
            </div>
            <span className="font-display text-[length:var(--fs-brand-compact)] font-bold tracking-[-0.04em] text-[var(--color-nav-text-on-accent)]">
              RiftHub
            </span>
          </Link>
          <span className="hidden font-mono text-[length:var(--fs-body-base)] text-[color:rgba(13,11,8,0.42)] sm:inline">
            |
          </span>
          <span className="font-mono text-[length:var(--fs-body-base)] tracking-[0.08em] text-[color:rgba(13,11,8,0.66)]">
            {post.comment_count} comments
          </span>
        </div>

        <Link
          href="/"
          className="font-mono text-[length:var(--fs-body-base)] tracking-[0.08em] text-[color:rgba(13,11,8,0.66)] transition-colors hover:text-[var(--color-nav-text-on-accent)]"
        >
          ← back
        </Link>
      </div>
    </header>
  );
}

export function PostHero({ post }: { post: PostPayload }) {
  const meta = [
    `${post.score} points`,
    `by ${post.author.username}`,
    formatRelativeTime(post.submitted_at),
    post.domain ? `(${post.domain.hostname})` : null,
  ].filter(Boolean);

  return (
    <section className="border-b border-[var(--color-border)] pb-10">
      <h1 className="max-w-5xl font-display text-[length:var(--fs-heading-hero)] leading-[1.18] tracking-[-0.04em] text-[var(--color-text)]">
        {post.title}
      </h1>

      <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-3 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        <VoteControl
          target="post"
          targetId={post.id}
          initialScore={post.score}
          initialViewerVote={post.viewer_vote as 1 | -1 | null}
          orientation="horizontal"
        />
        {meta.map((item) => (
          <span key={item}>{item}</span>
        ))}
        {post.url ? (
          <a
            href={post.url}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-[var(--color-accent)]"
          >
            →
          </a>
        ) : null}
      </div>

      {post.body_markdown ? (
        <div className="mt-8 max-w-4xl whitespace-pre-wrap font-display text-[length:var(--fs-body-comment)] leading-[1.9] text-[var(--color-text)]">
          {post.body_markdown}
        </div>
      ) : null}
    </section>
  );
}
