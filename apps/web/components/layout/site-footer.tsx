import Link from "next/link";

const FOOTER_LINKS = ["guidelines", "faq", "api", "security", "legal", "contact"];

export function SiteFooter() {
  return (
    <footer className="border-t border-(--color-border) px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-480">
        <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 font-mono text-xs text-(--color-text-dim)">
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link}
              href="#"
              className="transition-colors hover:text-orange-700"
            >
              {link}
            </Link>
          ))}
        </div>
        <p className="mt-8 text-center font-mono text-xs text-(--color-text-faint)">
          © 2026 RiftHub · All Rights Reserved
        </p>
      </div>
    </footer>
  );
}
