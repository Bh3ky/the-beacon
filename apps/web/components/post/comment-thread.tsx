"use client";

import { useState } from "react";

import { FlagAction } from "@/components/post/flag-action";
import { VoteControl } from "@/components/vote/vote-control";
import type { CommentNode } from "@/lib/comments";

import { CommentComposer } from "./comment-composer-shell";

const INDENT_COLORS = [
  "var(--indent-1)",
  "var(--indent-2)",
  "var(--indent-3)",
  "var(--indent-4)",
  "var(--indent-5)",
];

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
        <FlagAction targetType="comment" targetId={comment.id} subjectLabel="comment" />
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
  if (comments.length === 0) {
    return (
      <div className="border border-dashed border-[var(--color-border)] px-6 py-8 text-center">
        <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.18em] text-[var(--color-text-dim)]">
          No comments yet
        </p>
        <p className="mt-3 font-display text-[length:var(--fs-body-comment)] leading-[1.8] text-[var(--color-text)]">
          Start the discussion and shape how this story lands for everyone else.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {comments.map((comment) => (
        <CommentBranch key={comment.id} comment={comment} depth={0} />
      ))}
    </div>
  );
}
