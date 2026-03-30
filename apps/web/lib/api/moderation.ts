import { apiServerFetch } from "./server";
import type {
  FlagQueueResponse,
  IngestionReviewQueueResponse,
  SourceHealthResponse,
} from "./types";

export async function getModerationFlagQueue(limit = 50): Promise<FlagQueueResponse> {
  return apiServerFetch<FlagQueueResponse>(`/v1/moderation/flags?limit=${limit}`);
}

export async function getIngestionReviewQueue(limit = 50): Promise<IngestionReviewQueueResponse> {
  return apiServerFetch<IngestionReviewQueueResponse>(`/v1/moderation/ingestion/items?limit=${limit}`);
}

export async function getIngestionSourceHealth(
  limit = 20,
  failuresOnly = true,
): Promise<SourceHealthResponse> {
  return apiServerFetch<SourceHealthResponse>(
    `/v1/moderation/ingestion/sources?limit=${limit}&failures_only=${failuresOnly ? "true" : "false"}`,
  );
}
