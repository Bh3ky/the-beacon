import { apiFetch } from "./client";
import type { PlatformSummary } from "./types";

export async function getPlatformSummary(): Promise<PlatformSummary> {
  return apiFetch<PlatformSummary>("/v1/stats/summary");
}
