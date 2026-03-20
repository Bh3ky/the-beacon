"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { logout } from "@/lib/browser-api";
import { useCurrentUser } from "@/lib/use-current-user";

function formatJoinDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function HeaderAuth() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [loggingOut, setLoggingOut] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuError, setMenuError] = useState<string | null>(null);
  const [localUser, setLocalUser] = useState(user);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const avatarLabel = useMemo(() => {
    if (!localUser) {
      return "";
    }
    return localUser.username.slice(0, 2).toUpperCase();
  }, [localUser]);

  useEffect(() => {
    setLocalUser(user);
  }, [user]);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  async function handleLogout() {
    setLoggingOut(true);
    setMenuError(null);
    try {
      await logout();
      setLocalUser(null);
      setMenuOpen(false);
      router.replace("/");
      router.refresh();
    } catch {
      setMenuError("Could not log out right now.");
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

  if (!localUser) {
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
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => {
          setMenuError(null);
          setMenuOpen((open) => !open);
        }}
        aria-expanded={menuOpen}
        aria-haspopup="menu"
        className="flex h-11 w-11 items-center justify-center rounded-full border border-[rgba(13,11,8,0.18)] bg-[rgba(13,11,8,0.08)] font-mono text-(length:--fs-body-base) font-bold tracking-[0.08em] text-(--color-nav-text-on-accent) transition-colors hover:bg-[rgba(13,11,8,0.16)]"
      >
        {avatarLabel}
      </button>

      {menuOpen ? (
        <div className="absolute right-0 top-[calc(100%+0.9rem)] z-30 w-64 border border-(--color-border-strong) bg-(--color-surface) px-5 py-5 shadow-[0_20px_60px_rgba(0,0,0,0.32)]">
          <div className="flex flex-col items-center border-b border-(--color-border) pb-5 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full border border-(--color-border-strong) bg-[rgba(232,82,26,0.08)] font-mono text-(length:--fs-brand-compact) font-bold tracking-[0.08em] text-(--color-accent)">
              {avatarLabel}
            </div>
            <p className="mt-4 font-display text-(length:--fs-heading-success) tracking-[-0.03em] text-(--color-text)">
              {localUser.username}
            </p>
            <p className="mt-2 font-mono text-(length:--fs-meta) text-(--color-text-dim)">
              Joined {formatJoinDate(localUser.created_at)}
            </p>
          </div>

          <div className="pt-5 text-center">
            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className="font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base) text-(--color-text-dim) transition-colors hover:text-(--color-accent) disabled:cursor-wait disabled:text-(--color-text-faint)"
            >
              {loggingOut ? "logging out…" : "logout"}
            </button>
            {menuError ? (
              <p className="mt-3 font-mono text-(length:--fs-meta) text-(--color-error)">
                {menuError}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
