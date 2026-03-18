import Link from "next/link";

const NAV_ITEMS = [
  { href: "/", label: "top", active: true },
  { href: "/new", label: "new", active: false },
  { href: "/ask", label: "ask", active: false },
  { href: "/show", label: "show", active: false },
  { href: "/jobs", label: "jobs", active: false },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-[color:rgba(13,11,8,0.08)] bg-[var(--color-accent)]">
      <div className="mx-auto flex h-22 max-w-[120rem] items-center gap-6 px-6 sm:h-20 sm:px-10">
        <Link href="/" className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-[var(--color-nav-text-on-accent)] font-display font-bold text-[length:var(--fs-logo-letter)] text-[var(--color-accent)]">
            R
          </div>
          <span className="font-display font-bold tracking-[-0.04em] text-[length:var(--fs-heading-brand)] text-[var(--color-nav-text-on-accent)] sm:text-[length:var(--fs-heading-brand)]">
            Rift
          </span>
        </Link>

        <nav className="hidden items-center gap-10 md:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={[
                "border-b-2 pb-1 font-mono lowercase tracking-[0.06em] text-[length:var(--fs-body-base)]",
                item.active
                  ? "border-[var(--color-nav-text-on-accent)] text-[var(--color-nav-text-on-accent)]"
                  : "border-transparent text-[color:rgba(13,11,8,0.58)] transition-colors hover:text-[var(--color-nav-text-on-accent)]",
              ].join(" ")}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-5">
          <Link
            href="/submit"
            className="hidden font-mono lowercase tracking-[0.06em] text-[length:var(--fs-body-base)] text-[color:rgba(13,11,8,0.66)] transition-colors hover:text-[var(--color-nav-text-on-accent)] md:inline-flex"
          >
            submit
          </Link>
          <Link
            href="/login"
            className="rounded-md bg-[var(--color-nav-text-on-accent)] px-5 py-3 font-mono lowercase tracking-[0.06em] text-[length:var(--fs-body-base)] text-[var(--color-accent)] transition-transform hover:-translate-y-0.5"
          >
            login
          </Link>
        </div>
      </div>
    </header>
  );
}
