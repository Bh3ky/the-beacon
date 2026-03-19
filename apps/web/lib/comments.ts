import type { CommentPayload } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/feed";

export type CommentNode = {
  id: string;
  postId: string;
  parentCommentId: string | null;
  depth: number;
  body: string;
  author: string;
  score: number;
  viewerVote: 1 | -1 | null;
  time: string;
  isAuthor: boolean;
  replies: CommentNode[];
};

export function buildCommentTree(
  comments: CommentPayload[],
  options: {
    postAuthorUsername: string;
  },
): CommentNode[] {
  const { postAuthorUsername } = options;
  const nodes = new Map<string, CommentNode>();
  const roots: CommentNode[] = [];

  for (const comment of comments) {
    nodes.set(comment.id, {
      id: comment.id,
      postId: comment.post_id,
      parentCommentId: comment.parent_comment_id,
      depth: comment.depth,
      body: comment.body_markdown,
      author: comment.author.username,
      score: comment.score,
      viewerVote: comment.viewer_vote,
      time: formatRelativeTime(comment.created_at),
      isAuthor: comment.author.username === postAuthorUsername,
      replies: [],
    });
  }

  for (const comment of comments) {
    const node = nodes.get(comment.id);
    if (!node) {
      continue;
    }

    if (comment.parent_comment_id) {
      const parent = nodes.get(comment.parent_comment_id);
      if (parent) {
        parent.replies.push(node);
        continue;
      }
    }

    roots.push(node);
  }

  return roots;
}
