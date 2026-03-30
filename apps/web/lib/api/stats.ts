import { apiServerFetch } from "./server";
import type { PlatformSummary } from "./types";

export async function getPlatformSummary(): Promise<PlatformSummary> {
  return apiServerFetch<PlatformSummary>("/v1/stats/summary");
}
