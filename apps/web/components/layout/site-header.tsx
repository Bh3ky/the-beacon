import Image from "next/image";
import Link from "next/link";

import { HeaderAuth } from "@/components/auth/header-auth";
import logoImage from "../../../../public/rifthub-logo.png";

const NAV_ITEMS = [
  { href: "/", label: "top", enabled: true },
  { href: "/new", label: "new", enabled: true },
  { href: "/ask", label: "ask", enabled: true },
  { href: "/show", label: "show", enabled: true },
  { href: "/jobs", label: "jobs", enabled: true },
];

type ActiveTab = "top" | "new" | "ask" | "show" | "jobs" | null;

export function SiteHeader({ activeTab = "top" }: { activeTab?: ActiveTab }) {
  return (
    <header className="sticky top-0 z-50 border-b border-[rgba(13,11,8,0.08)] bg-(--color-accent)">
      <div className="mx-auto flex h-22 max-w-480 items-center gap-6 px-6 sm:h-20 sm:px-10">
        <Link href="/" className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-md bg-(--color-nav-text-on-accent)">
            <Image
              src={logoImage}
              alt="RiftHub logo"
              width={48}
              height={48}
              className="h-full w-full object-cover"
              priority
            />
          </div>
          <span className="font-display font-bold tracking-[-0.04em] text-(length:--fs-heading-brand) text-(--color-nav-text-on-accent) sm:text-(length:--fs-heading-brand)">
            RiftHub
          </span>
        </Link>

        <nav className="hidden items-center gap-10 md:flex">
          {NAV_ITEMS.map((item) => (
            item.enabled && item.href ? (
              <Link
                key={item.label}
                href={item.href}
                className={[
                  "border-b-2 pb-1 font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base)",
                  activeTab === item.label
                    ? "border-(--color-nav-text-on-accent) text-(--color-nav-text-on-accent)"
                    : "border-transparent text-[rgba(13,11,8,0.58)] transition-colors hover:text-(--color-nav-text-on-accent)",
                ].join(" ")}
              >
                {item.label}
              </Link>
            ) : (
              <span
                key={item.label}
                className="border-b-2 border-transparent pb-1 font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base) text-[rgba(13,11,8,0.42)]"
              >
                {item.label}
              </span>
            )
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-5">
          <Link
            href="/submit"
            className="hidden font-mono lowercase tracking-[0.06em] text-(length:--fs-body-base) text-black transition-colors hover:text-(--color-nav-text-on-accent) md:inline-flex"
          >
            submit
          </Link>
          <HeaderAuth />
        </div>
      </div>
    </header>
  );
}
