"use client";

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import {
  BrowserApiError,
  removeCommentVote,
  removePostVote,
  voteOnComment,
  voteOnPost,
} from "@/lib/browser-api";

type VoteTarget = "post" | "comment";

type VoteControlProps = {
  target: VoteTarget;
  targetId: string;
  initialScore: number;
  initialViewerVote: 1 | -1 | null;
  orientation?: "vertical" | "horizontal";
  compact?: boolean;
};

export function VoteControl({
  target,
  targetId,
  initialScore,
  initialViewerVote,
  orientation = "vertical",
  compact = false,
}: VoteControlProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [score, setScore] = useState(initialScore);
  const [viewerVote, setViewerVote] = useState<1 | -1 | null>(initialViewerVote);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function applyVote(voteValue: 1 | -1) {
    setBusy(true);
    setError(null);

    try {
      if (target === "post") {
        const response =
          viewerVote === voteValue
            ? await removePostVote(targetId)
            : await voteOnPost(targetId, voteValue);
        setScore(response.post.score);
        setViewerVote(response.post.viewer_vote);
      } else {
        const response =
          viewerVote === voteValue
            ? await removeCommentVote(targetId)
            : await voteOnComment(targetId, voteValue);
        setScore(response.comment.score);
        setViewerVote(response.comment.viewer_vote);
      }
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
          : "Vote failed. Try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  const layoutClass =
    orientation === "horizontal"
      ? "flex items-center gap-3"
      : "flex flex-col items-center gap-1.5";

  const buttonClass =
    "font-mono transition-colors hover:text-[var(--color-accent)] disabled:cursor-wait disabled:text-[var(--color-text-dim)]";

  const sizeClass = compact
    ? "text-[length:var(--fs-meta)]"
    : "text-[length:var(--fs-body-base)]";

  return (
    <div className={layoutClass}>
      <button
        type="button"
        aria-label="Upvote"
        disabled={busy}
        onClick={() => applyVote(1)}
        className={[
          buttonClass,
          sizeClass,
          viewerVote === 1 ? "text-[var(--color-accent)]" : "text-[var(--color-text-dim)]",
        ].join(" ")}
      >
        ▲
      </button>

      <span
        className={[
          "font-mono",
          sizeClass,
          viewerVote === 1
            ? "text-[var(--color-accent)]"
            : viewerVote === -1
              ? "text-[var(--color-error)]"
              : "text-[var(--color-text-muted)]",
        ].join(" ")}
      >
        {score}
      </span>

      <button
        type="button"
        aria-label="Downvote"
        disabled={busy}
        onClick={() => applyVote(-1)}
        className={[
          buttonClass,
          sizeClass,
          viewerVote === -1 ? "text-[var(--color-error)]" : "text-[var(--color-text-dim)]",
        ].join(" ")}
      >
        ▼
      </button>

      {error ? (
        <span className="font-mono text-[length:var(--fs-label)] text-[var(--color-error)]">
          {error}
        </span>
      ) : null}
    </div>
  );
}
