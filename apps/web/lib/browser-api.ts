"use client";

import type {
  AuthenticatedResponse,
  CommentResponse,
  CommentVoteResponse,
  PostResponse,
  PostVoteResponse,
  RegisterResponse,
} from "@/lib/api/types";

const CSRF_COOKIE_NAME = "rifthub_csrf";

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export class BrowserApiError extends Error {
  status: number;
  code: string | null;
  details: unknown;

  constructor(status: number, message: string, code: string | null, details: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const value = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${name}=`))
    ?.split("=")[1];
  return value ? decodeURIComponent(value) : null;
}

export async function browserApiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("accept", "application/json");

  if (init.body && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrfToken = readCookie(CSRF_COOKIE_NAME);
    if (csrfToken && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(`/api/${path.replace(/^\/+/, "")}`, {
    ...init,
    method,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const rawText = await response.text();
  const parsed = rawText ? (JSON.parse(rawText) as T & ErrorEnvelope) : undefined;

  if (!response.ok) {
    const errorBody = parsed as ErrorEnvelope | undefined;
    throw new BrowserApiError(
      response.status,
      errorBody?.error?.message ?? `Request failed with status ${response.status}.`,
      errorBody?.error?.code ?? null,
      errorBody?.error?.details ?? null,
    );
  }

  return parsed as T;
}

export async function fetchCurrentUser(): Promise<AuthenticatedResponse["user"] | null> {
  try {
    const response = await browserApiFetch<AuthenticatedResponse>("auth/me");
    return response.user;
  } catch (error) {
    if (error instanceof BrowserApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export async function login(payload: {
  email: string;
  password: string;
}): Promise<AuthenticatedResponse> {
  return browserApiFetch<AuthenticatedResponse>("auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function register(payload: {
  username: string;
  email: string;
  password: string;
}): Promise<RegisterResponse> {
  return browserApiFetch<RegisterResponse>("auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function resendVerification(payload: {
  email: string;
}): Promise<void> {
  return browserApiFetch<void>("auth/resend-verification", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function verifyAccount(payload: {
  token: string;
}): Promise<AuthenticatedResponse> {
  return browserApiFetch<AuthenticatedResponse>("auth/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logout(): Promise<void> {
  return browserApiFetch<void>("auth/logout", {
    method: "POST",
  });
}

export async function submitPost(payload: {
  post_type: "link" | "text" | "job";
  category: string;
  title: string;
  url?: string | null;
  body_markdown?: string | null;
  job_expires_at?: string | null;
}): Promise<PostResponse> {
  return browserApiFetch<PostResponse>("posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createComment(payload: {
  postId: string;
  body_markdown: string;
  parent_comment_id?: string | null;
}): Promise<CommentResponse> {
  return browserApiFetch<CommentResponse>(`posts/${payload.postId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      body_markdown: payload.body_markdown,
      parent_comment_id: payload.parent_comment_id ?? null,
    }),
  });
}

export async function voteOnPost(postId: string, voteValue: 1 | -1): Promise<PostVoteResponse> {
  return browserApiFetch<PostVoteResponse>(`posts/${postId}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_value: voteValue }),
  });
}

export async function removePostVote(postId: string): Promise<PostVoteResponse> {
  return browserApiFetch<PostVoteResponse>(`posts/${postId}/vote`, {
    method: "DELETE",
  });
}

export async function voteOnComment(
  commentId: string,
  voteValue: 1 | -1,
): Promise<CommentVoteResponse> {
  return browserApiFetch<CommentVoteResponse>(`comments/${commentId}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_value: voteValue }),
  });
}

export async function removeCommentVote(commentId: string): Promise<CommentVoteResponse> {
  return browserApiFetch<CommentVoteResponse>(`comments/${commentId}/vote`, {
    method: "DELETE",
  });
}
