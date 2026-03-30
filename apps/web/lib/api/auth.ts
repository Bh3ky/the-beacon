import { ApiFetchError } from "./client";
import { apiServerFetch } from "./server";
import type { AuthenticatedResponse } from "./types";

export async function getCurrentUserServer(): Promise<AuthenticatedResponse["user"] | null> {
  try {
    const response = await apiServerFetch<AuthenticatedResponse>("/v1/auth/me");
    return response.user;
  } catch (error) {
    if (error instanceof ApiFetchError && error.status === 401) {
      return null;
    }
    throw error;
  }
}
