import Link from "next/link";

export function FeedPaginationLink({ href }: { href: string }) {
  return (
    <div className="pt-10 pl-[calc(2rem+2.5rem+2rem)]">
      <Link
        href={href}
        className="group inline-flex items-baseline gap-2 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-accent)] focus-visible:text-[var(--color-accent)]"
      >
        <span className="transition-colors group-hover:text-[var(--color-accent)] group-focus-visible:text-[var(--color-accent)]">
          more
        </span>
        <span
          aria-hidden="true"
          className="transition-colors group-hover:text-[var(--color-accent)] group-focus-visible:text-[var(--color-accent)]"
        >
          →
        </span>
      </Link>
    </div>
  );
}
