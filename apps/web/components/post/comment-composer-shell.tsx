"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { BrowserApiError, createComment } from "@/lib/browser-api";
import { useCurrentUser } from "@/lib/use-current-user";

type CommentComposerProps = {
  postId: string;
  parentCommentId?: string | null;
  compact?: boolean;
  buttonLabel?: string;
  onSubmitted?: () => void;
};

export function CommentComposer({
  postId,
  parentCommentId = null,
  compact = false,
  buttonLabel = "add comment",
  onSubmitted,
}: CommentComposerProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading } = useCurrentUser();
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await createComment({
        postId,
        body_markdown: body,
        parent_comment_id: parentCommentId,
      });
      setBody("");
      onSubmitted?.();
      router.refresh();
    } catch (errorValue) {
      if (
        errorValue instanceof BrowserApiError &&
        (errorValue.status === 401 || errorValue.status === 403)
      ) {
        router.push(`/login?next=${encodeURIComponent(pathname || "/")}`);
        return;
      }
      setError(
        errorValue instanceof BrowserApiError
          ? errorValue.message
          : "Comment submission failed. Try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        Checking session…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <div className="rounded-sm border border-[var(--color-border-strong)] bg-[var(--color-bg)] p-0">
          <div className="min-h-[8rem] px-5 py-5 font-mono text-[length:var(--fs-body-input)] text-[var(--color-text-muted)]">
            Share your perspective...
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-5">
          <Link
            href={`/login?next=${encodeURIComponent(pathname || "/")}`}
            className="inline-flex items-center bg-[var(--color-accent)] px-7 py-4 font-mono text-[length:var(--fs-body-base)] font-bold uppercase tracking-[0.1em] text-[var(--color-nav-text-on-accent)] transition-colors hover:bg-[var(--color-accent-hover)]"
          >
            sign in to comment
          </Link>
          <p className="font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
            You need a live browser session to join the thread.
          </p>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="rounded-sm border border-[var(--color-border-strong)] bg-[var(--color-bg)] p-0">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder={compact ? "Write a reply…" : "Share your perspective..."}
          className={[
            "w-full resize-y border-0 bg-transparent px-5 py-5 font-mono text-[length:var(--fs-body-input)] text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-muted)]",
            compact ? "min-h-[8rem]" : "min-h-[13rem]",
          ].join(" ")}
        />
      </div>

      {error ? (
        <p className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-error)]">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-5">
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center bg-[var(--color-accent)] px-7 py-4 font-mono text-[length:var(--fs-body-base)] font-bold uppercase tracking-[0.1em] text-[var(--color-nav-text-on-accent)] transition-colors hover:bg-[var(--color-accent-hover)] disabled:cursor-wait disabled:bg-[var(--color-accent-dim)]"
        >
          {submitting ? "posting…" : buttonLabel}
        </button>
        {!compact ? (
          <p className="font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
            Signed in as {user.username}
          </p>
        ) : null}
      </div>
    </form>
  );
}
