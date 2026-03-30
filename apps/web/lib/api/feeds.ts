import { apiServerFetch } from "./server";
import type { FeedResponse } from "./types";

function withFeedQuery(limit: number, cursor?: string): string {
  const query = new URLSearchParams({ limit: String(limit) });
  if (cursor) {
    query.set("cursor", cursor);
  }
  return query.toString();
}

export async function getNewFeed(limit = 30, cursor?: string): Promise<FeedResponse> {
  return apiServerFetch<FeedResponse>(`/v1/feeds/new?${withFeedQuery(limit, cursor)}`);
}

export async function getJobsFeed(limit = 30, cursor?: string): Promise<FeedResponse> {
  return apiServerFetch<FeedResponse>(`/v1/feeds/jobs?${withFeedQuery(limit, cursor)}`);
}

export async function getAskFeed(limit = 30, cursor?: string): Promise<FeedResponse> {
  return apiServerFetch<FeedResponse>(`/v1/feeds/ask?${withFeedQuery(limit, cursor)}`);
}

export async function getShowFeed(limit = 30, cursor?: string): Promise<FeedResponse> {
  return apiServerFetch<FeedResponse>(`/v1/feeds/show?${withFeedQuery(limit, cursor)}`);
}

export async function getTopFeedPage(limit = 30, cursor?: string): Promise<FeedResponse> {
  return apiServerFetch<FeedResponse>(`/v1/feeds/top?${withFeedQuery(limit, cursor)}`);
}
