"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { logout } from "@/lib/browser-api";
import { useCurrentUser } from "@/lib/use-current-user";

export function HeaderAuth() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      router.push("/");
      router.refresh();
    } finally {
      setLoggingOut(false);
    }
  }

  if (loading) {
    return (
      <div className="font-mono text-(length:--fs-body-base) text-[rgba(13,11,8,0.58)]">
        session…
      </div>
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="rounded-md bg-(--color-nav-text-on-accent) px-5 py-3 font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base) text-orange-700 transition-transform hover:-translate-y-0.5"
      >
        login
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <span className="hidden font-mono text-(length:--fs-body-base) text-(--color-nav-text-on-accent) md:inline">
        {user.username}
      </span>
      <button
        type="button"
        onClick={handleLogout}
        disabled={loggingOut}
        className="font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base) text-[rgba(13,11,8,0.66)] transition-colors hover:text-(--color-nav-text-on-accent) disabled:cursor-wait disabled:text-[rgba(13,11,8,0.42)]"
      >
        {loggingOut ? "logging out…" : "logout"}
      </button>
    </div>
  );
}
