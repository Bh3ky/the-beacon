import { apiFetch } from "./client";
import type { CommentListResponse, PostResponse } from "./types";

export async function getPostDetail(postId: string): Promise<PostResponse> {
  return apiFetch<PostResponse>(`/v1/posts/${postId}`);
}

export async function getPostComments(
  postId: string,
  sort: "top" | "new" | "old" = "top",
): Promise<CommentListResponse> {
  return apiFetch<CommentListResponse>(`/v1/posts/${postId}/comments?sort=${sort}`);
}
