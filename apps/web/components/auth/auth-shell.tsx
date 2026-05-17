import Image from "next/image";
import Link from "next/link";
import logoImage from "../../../../public/rifthub-logo.png";

import { AppShell } from "@/components/layout/app-shell";

const REVIEWS = [
  {
    quote: "Finally a feed that surfaces what builders across the continent are actually discussing.",
    author: "nairobidev",
    region: "Kenya",
  },
  {
    quote: "The signal feels sharper here. You can tell it is shaped by operators, not engagement bait.",
    author: "fintech_ng",
    region: "Nigeria",
  },
  {
    quote: "I use RiftHub to track product moves, funding signals, and talent shifts without the noise.",
    author: "cairo_startup",
    region: "Egypt",
  },
] as const;

export async function AuthShell({
  activeTab,
  heading,
  subheading,
  children,
}: {
  activeTab: "login" | "register";
  heading: string;
  subheading?: string;
  children: React.ReactNode;
}) {
  return (
    <AppShell>
      <div className="flex flex-1 flex-col">
        <section className="relative flex-1 overflow-hidden border-b border-(--color-border)">
          <div
            className="absolute inset-0 opacity-25"
            style={{
              backgroundImage:
                "linear-gradient(rgba(42,34,24,0.7) 1px, transparent 1px), linear-gradient(90deg, rgba(42,34,24,0.7) 1px, transparent 1px)",
              backgroundSize: "44px 44px",
            }}
          />

          <div className="relative z-10 px-8 py-8 lg:px-10 lg:py-10">
            <div className="mx-auto flex w-full max-w-5xl flex-col">
              <div className="flex items-center gap-4">
                <Link href="/" className="flex items-center gap-4">
                  <div className="h-13 w-13 overflow-hidden rounded-md border border-(--color-text-dim) bg-transparent">
                    <Image
                      src={logoImage}
                      alt="RiftHub logo"
                      width={52}
                      height={52}
                      className="h-full w-full object-cover"
                      priority
                    />
                  </div>
                  <span className="font-display text-[1.25rem] font-bold tracking-[-0.05em] text-(--color-text-dim)">
                    RiftHub
                  </span>
                </Link>
              </div>

              <div className="mx-auto mt-5 max-w-3xl text-center">
                <h1 className="font-display text-2xl leading-[1.18] tracking-[-0.05em] text-(--color-text)">
                  Cut through the noise. <br />
                  Get closer to the{" "}
                  <span className="italic text-(--color-accent)">signal</span>.
                </h1>
                <p className="mx-auto mt-8 max-w-2xl whitespace-pre-line font-mono text-xs leading-[1.85] text-(--color-text-muted)">
                  One feed. Zero algorithm.
                  {"\n"}
                  Real-time insights from the builders and founders shaping Africa's ecosystem.
                </p>
              </div>

              <div className="mx-auto mt-16 w-full max-w-md border border-(--color-border-strong) bg-[rgba(13,11,8,0.58)] px-6 py-8 shadow-[0_24px_80px_rgba(0,0,0,0.28)] backdrop-blur-[2px] sm:px-8 sm:py-10">
                <div className="flex border-b border-(--color-border)">
                  <Link
                    href="/login"
                    className={[
                      "flex-1 border-b-2 px-6 py-2 text-center font-mono text-xs lowercase tracking-[0.08em]",
                      activeTab === "login"
                        ? "border-(--color-accent) text-(--color-accent)"
                        : "border-transparent text-(--color-text-dim) hover:text-(--color-text-muted)",
                    ].join(" ")}
                  >
                    sign in
                  </Link>
                  <Link
                    href="/register"
                    className={[
                      "flex-1 border-b-2 px-6 py-2 text-center font-mono text-xs lowercase tracking-[0.08em]",
                      activeTab === "register"
                        ? "border-(--color-accent) text-(--color-accent)"
                        : "border-transparent text-(--color-text-dim) hover:text-(--color-text-muted)",
                    ].join(" ")}
                  >
                    create account
                  </Link>
                </div>

                <div className="pt-8">
                  <h2 className="text-center font-display text-lg tracking-[-0.04em] text-(--color-text)">
                    {heading}
                  </h2>
                  {subheading ? (
                    <p className="mx-auto mt-4 max-w-lg text-center font-mono text-(length:--fs-body-base) leading-7 text-(--color-text-dim)">
                      {subheading}
                    </p>
                  ) : null}
                  <div className="mt-4">{children}</div>
                </div>
              </div>

              <div className="mx-auto mt-16 grid w-full max-w-6xl gap-6 lg:grid-cols-3">
                {REVIEWS.map((review) => (
                  <article
                    key={`${review.author}-${review.region}`}
                    className="border border-(--color-border-strong) bg-[rgba(17,14,11,0.72)] px-7 py-7 shadow-[0_18px_50px_rgba(0,0,0,0.24)]"
                  >
                    <p className="font-display text-(length:--fs-body-comment) italic leading-[1.8] text-(--color-text)">
                      “{review.quote}”
                    </p>
                    <p className="mt-6 font-mono text-(length:--fs-body-base) text-(--color-accent)">
                      {review.author}
                    </p>
                    <p className="mt-1 font-mono text-(length:--fs-meta) text-(--color-text-dim)">
                      {review.region}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <footer className="mt-auto flex flex-wrap justify-between gap-4 border-t border-(--color-border) px-8 py-6 font-mono text-(length:--fs-meta) text-(--color-text-dim) lg:px-10">
          <span>© 2026 RiftHub · All Rights Reserved</span>
          <div className="flex gap-6">
            <Link href="#" className="hover:text-(--color-accent)">
              guidelines
            </Link>
            <Link href="#" className="hover:text-(--color-accent)">
              privacy
            </Link>
            <Link href="#" className="hover:text-(--color-accent)">
              contact
            </Link>
          </div>
        </footer>
      </div>
    </AppShell>
  );
}
