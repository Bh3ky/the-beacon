import Link from "next/link";

const FOOTER_LINKS = ["guidelines", "faq", "api", "security", "legal", "contact"];

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--color-border)] px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-[120rem]">
        <div className="flex flex-wrap justify-center gap-x-10 gap-y-4 font-mono text-2xl text-[var(--color-text-dim)]">
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link}
              href="#"
              className="transition-colors hover:text-[var(--color-accent)]"
            >
              {link}
            </Link>
          ))}
        </div>
        <p className="mt-8 text-center font-mono text-xl text-[var(--color-text-faint)]">
          Rift · Built for the African tech ecosystem
        </p>
      </div>
    </footer>
  );
}
