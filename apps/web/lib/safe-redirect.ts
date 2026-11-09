// A throwaway address, used only to ask "does this stay on our own site?".
const FAKE_BASE = "http://rifthub.invalid";

/**
 * Turn a user-supplied "?next=" value into a path that is safe to redirect to.
 * Anything that would leave our site (https://evil.com, //evil.com, javascript:...)
 * becomes "/".
 */
export function safeRedirectPath(next: string | null | undefined): string {
  // Only paths that start with "/" are accepted, e.g. "/post/1/hello".
  if (!next || !next.startsWith("/")) {
    return "/";
  }

  try {
    const parsed = new URL(next, FAKE_BASE);
    if (parsed.origin !== FAKE_BASE) {
      return "/";
    }
    return parsed.pathname + parsed.search + parsed.hash;
  } catch {
    return "/";
  }
}
