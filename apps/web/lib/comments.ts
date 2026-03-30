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
  rankScore: number;
  createdAt: string;
};

export function buildCommentTree(
  comments: CommentPayload[],
  options: {
    postAuthorUsername: string;
    sort?: "top" | "new" | "old";
  },
): CommentNode[] {
  const { postAuthorUsername, sort = "top" } = options;
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
      rankScore: comment.rank_score,
      createdAt: comment.created_at,
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

  if (sort === "top") {
    sortCommentNodes(roots);
  }

  return roots;
}

function compareCommentNodes(left: CommentNode, right: CommentNode): number {
  if (left.rankScore !== right.rankScore) {
    return right.rankScore - left.rankScore;
  }

  if (left.createdAt !== right.createdAt) {
    return right.createdAt.localeCompare(left.createdAt);
  }

  return right.id.localeCompare(left.id);
}

function sortCommentNodes(nodes: CommentNode[]): void {
  nodes.sort(compareCommentNodes);
  for (const node of nodes) {
    if (node.replies.length > 0) {
      sortCommentNodes(node.replies);
    }
  }
}
