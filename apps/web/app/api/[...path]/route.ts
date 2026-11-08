import type { NextRequest } from "next/server";

import { getApiBaseUrl } from "@/lib/api/client";

export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const targetPath = path.join("/");
  const targetUrl = `${getApiBaseUrl()}/v1/${targetPath}${request.nextUrl.search}`;

  const headers = new Headers();
  // Never pass the browser's own IP headers through: the browser can fake them.
  const dropHeaders = ["host", "connection", "content-length", "x-forwarded-for", "x-real-ip", "forwarded", "x-proxy-secret"];
  request.headers.forEach((value, key) => {
    if (dropHeaders.includes(key.toLowerCase())) {
      return;
    }
    headers.set(key, value);
  });

  // On Vercel, x-forwarded-for is overwritten with the real client IP before
  // it reaches us. Take the LAST entry: that is the one our platform added.
  const platformIp = request.headers.get("x-forwarded-for")?.split(",").at(-1)?.trim();
  if (platformIp) {
    headers.set("x-forwarded-for", platformIp);
  }
  const proxySecret = process.env.RIFTHUB_PROXY_SECRET;
  if (proxySecret) {
    headers.set("x-proxy-secret", proxySecret);
  }


  const method = request.method.toUpperCase();
  const body =
    method === "GET" || method === "HEAD" || method === "OPTIONS"
      ? undefined
      : await request.text();

  const upstream = await fetch(targetUrl, {
    method,
    headers,
    body,
    cache: "no-store",
    redirect: "manual",
  });

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (["connection", "content-encoding", "content-length", "set-cookie", "transfer-encoding"].includes(lower)) {
      return;
    }
    responseHeaders.set(key, value);
  });

  const upstreamHeaders = upstream.headers as Headers & {
    getSetCookie?: () => string[];
  };

  if (typeof upstreamHeaders.getSetCookie === "function") {
    for (const cookie of upstreamHeaders.getSetCookie()) {
      responseHeaders.append("set-cookie", cookie);
    }
  } else {
    const cookie = upstream.headers.get("set-cookie");
    if (cookie) {
      responseHeaders.append("set-cookie", cookie);
    }
  }

  return new Response(method === "HEAD" ? null : upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
