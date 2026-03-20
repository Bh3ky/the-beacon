"use client";

import { useState } from "react";

import { VoteControl } from "@/components/vote/vote-control";
import { BrowserApiError, createFlag } from "@/lib/browser-api";
import type { CommentNode } from "@/lib/comments";

import { CommentComposer } from "./comment-composer-shell";

const INDENT_COLORS = [
  "var(--indent-1)",
  "var(--indent-2)",
  "var(--indent-3)",
  "var(--indent-4)",
  "var(--indent-5)",
];

const FLAG_REASONS = [
  { value: "spam", label: "spam" },
  { value: "abuse", label: "abuse" },
  { value: "misinformation", label: "misinformation" },
  { value: "off_topic", label: "off-topic" },
  { value: "other", label: "other" },
] as const;

function CommentFlagAction({ commentId }: { commentId: string }) {
  const [showFlagForm, setShowFlagForm] = useState(false);
  const [reasonCode, setReasonCode] =
    useState<(typeof FLAG_REASONS)[number]["value"]>("spam");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await createFlag({
        target_type: "comment",
        target_id: commentId,
        reason_code: reasonCode,
        notes,
      });
      setSuccessMessage("comment reported");
      setShowFlagForm(false);
      setNotes("");
    } catch (error) {
      if (error instanceof BrowserApiError) {
        if (error.status === 401) {
          setErrorMessage("sign in to report this comment");
        } else if (error.code === "duplicate_open_flag") {
          setErrorMessage("you already reported this reason");
        } else {
          setErrorMessage(error.message.toLowerCase());
        }
      } else {
        setErrorMessage("could not submit report");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          setShowFlagForm((current) => !current);
          setErrorMessage(null);
          setSuccessMessage(null);
        }}
        className="transition-colors hover:text-[var(--color-accent)]"
      >
        flag
      </button>

      {successMessage ? (
        <p className="mt-3 font-mono text-[length:var(--fs-meta)] text-[var(--color-accent)]">
          {successMessage}
        </p>
      ) : null}

      {showFlagForm ? (
        <form onSubmit={handleSubmit} className="mt-4 space-y-4 border-t border-[var(--color-border)] pt-4">
          <label className="block">
            <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
              reason
            </span>
            <select
              value={reasonCode}
              onChange={(event) => setReasonCode(event.target.value as typeof reasonCode)}
              className="mt-2 w-full border border-[var(--color-border)] bg-[rgba(13,11,8,0.7)] px-3 py-3 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text)] outline-none transition-colors focus:border-[var(--color-accent)]"
            >
              {FLAG_REASONS.map((reason) => (
                <option key={reason.value} value={reason.value}>
                  {reason.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block font-mono text-[length:var(--fs-label)] uppercase tracking-[0.16em] text-[var(--color-text-dim)]">
              notes
            </span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              className="mt-2 w-full resize-y border border-[var(--color-border)] bg-[rgba(13,11,8,0.7)] px-3 py-3 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text)] outline-none transition-colors focus:border-[var(--color-accent)]"
              placeholder="optional context"
            />
          </label>

          {errorMessage ? (
            <p className="font-mono text-[length:var(--fs-meta)] text-[var(--color-error)]">
              {errorMessage}
            </p>
          ) : null}

          <div className="flex items-center gap-4 font-mono text-[length:var(--fs-meta)]">
            <button
              type="submit"
              disabled={submitting}
              className="text-[var(--color-accent)] transition-colors hover:text-[var(--color-accent-hover)] disabled:cursor-wait disabled:text-[var(--color-text-dim)]"
            >
              {submitting ? "sending…" : "submit report"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowFlagForm(false);
                setErrorMessage(null);
              }}
              className="text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-text)]"
            >
              cancel
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}

function CommentBody({
  comment,
  depth,
  bordered = false,
}: {
  comment: CommentNode;
  depth: number;
  bordered?: boolean;
}) {
  const [showReply, setShowReply] = useState(false);

  return (
    <div
      className={[
        bordered
          ? "border border-[var(--color-border)] bg-[var(--color-surface)] px-7 py-7"
          : "px-0 py-0",
      ].join(" ")}
    >
      <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-2 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        <span className="text-[var(--color-text-dim)]">[-]</span>
        <span
          className={[
            "font-bold",
            comment.isAuthor ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)]",
          ].join(" ")}
        >
          {comment.author}
        </span>
        {comment.isAuthor ? (
          <span className="rounded-sm bg-[color:rgba(232,82,26,0.12)] px-2 py-1 text-[length:var(--fs-badge)] uppercase tracking-[0.16em] text-[var(--color-accent)]">
            author
          </span>
        ) : null}
        <span>{comment.time}</span>
        <VoteControl
          target="comment"
          targetId={comment.id}
          initialScore={comment.score}
          initialViewerVote={comment.viewerVote}
          orientation="horizontal"
          compact
        />
      </div>

      <p className="whitespace-pre-wrap font-display text-[length:var(--fs-body-comment)] leading-[1.9] tracking-[-0.01em] text-[var(--color-text)]">
        {comment.body}
      </p>

      <div className="mt-6 flex gap-8 font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
        <button
          type="button"
          onClick={() => setShowReply((current) => !current)}
          className="transition-colors hover:text-[var(--color-accent)]"
        >
          {showReply ? "cancel" : "reply"}
        </button>
        <span>share</span>
        <CommentFlagAction commentId={comment.id} />
      </div>

      {showReply ? (
        <div className="mt-6 border-t border-[var(--color-border)] pt-6">
          <CommentComposer
            postId={comment.postId}
            parentCommentId={comment.id}
            compact
            buttonLabel="reply"
            onSubmitted={() => setShowReply(false)}
          />
        </div>
      ) : null}

      {comment.replies.length > 0 ? (
        <div className="mt-8 space-y-8">
          {comment.replies.map((reply) => (
            <CommentBranch key={reply.id} comment={reply} depth={depth + 1} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function CommentBranch({
  comment,
  depth,
}: {
  comment: CommentNode;
  depth: number;
}) {
  const indentColor = INDENT_COLORS[Math.min(depth, INDENT_COLORS.length - 1)];

  if (depth === 0) {
    return <CommentBody comment={comment} depth={depth} />;
  }

  return (
    <div className="flex gap-6">
      <div className="flex w-8 min-w-8 justify-center">
        <div className="w-px opacity-45" style={{ backgroundColor: indentColor }} />
      </div>

      <div className="min-w-0 flex-1">
        <CommentBody comment={comment} depth={depth} />
      </div>
    </div>
  );
}

export function CommentThread({ comments }: { comments: CommentNode[] }) {
  return (
    <div className="space-y-8">
      {comments.map((comment) => (
        <CommentBranch key={comment.id} comment={comment} depth={comment.depth} />
      ))}
    </div>
  );
}
