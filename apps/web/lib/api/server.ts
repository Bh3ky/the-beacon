import "server-only";

import { cookies } from "next/headers";

import { ApiFetchError, getApiBaseUrl } from "./client";

export async function apiServerFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const requestCookies = await cookies();
  const headers = new Headers(init?.headers);
  const cookieHeader = requestCookies.toString();

  headers.set("accept", "application/json");

  if (cookieHeader && !headers.has("cookie")) {
    headers.set("cookie", cookieHeader);
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiFetchError(
      response.status,
      `API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as T;
}
