import { FeedRow, type FeedRowModel } from "@/components/feed/feed-row";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { StatsStrip } from "@/components/layout/stats-strip";

const POSTS: FeedRowModel[] = [
  {
    id: 1,
    title: "Flutterwave raises $17M to expand payment infrastructure across West Africa",
    domain: "techcrunch.com",
    points: 312,
    author: "builderzw",
    time: "4 hours ago",
    comments: 87,
    category: "funding",
  },
  {
    id: 2,
    title: "Show Rift: I built an open-source M-Pesa SDK for Node.js developers",
    domain: "github.com",
    points: 284,
    author: "nairobidev",
    time: "6 hours ago",
    comments: 63,
    category: "show",
  },
  {
    id: 3,
    title: "Why African founders should stop building for Silicon Valley and start building for Accra",
    domain: "medium.com",
    points: 241,
    author: "kofi_atta",
    time: "8 hours ago",
    comments: 112,
    category: "opinion",
  },
  {
    id: 4,
    title: "Nigeria's SEC releases updated framework for crypto regulation in 2025",
    domain: "sec.gov.ng",
    points: 198,
    author: "fintech_ng",
    time: "10 hours ago",
    comments: 45,
    category: "policy",
  },
  {
    id: 5,
    title: "Ask Rift: Best local cloud hosting options for early-stage African startups?",
    domain: null,
    points: 176,
    author: "bheki_dev",
    time: "11 hours ago",
    comments: 94,
    category: "ask",
  },
  {
    id: 6,
    title: "Andela is now placing engineers across 100+ African companies — the model has shifted",
    domain: "andela.com",
    points: 154,
    author: "talentwatch",
    time: "13 hours ago",
    comments: 38,
    category: "news",
  },
  {
    id: 7,
    title: "The infrastructure problem: why payments still fail at 2AM across the continent",
    domain: "substack.com",
    points: 143,
    author: "infrabuilder",
    time: "14 hours ago",
    comments: 71,
    category: "opinion",
  },
  {
    id: 8,
    title: "Show Rift: Rift — a Hacker News for African tech (we're building this live)",
    domain: "getrift.africa",
    points: 398,
    author: "bheki_dev",
    time: "just now",
    comments: 0,
    category: "show",
  },
  {
    id: 9,
    title: "Egypt's fintech Paymob crosses 250k merchants — largest POS network in MENA-Africa",
    domain: "paymob.com",
    points: 129,
    author: "cairo_startup",
    time: "16 hours ago",
    comments: 29,
    category: "funding",
  },
  {
    id: 10,
    title: "Job: Senior Backend Engineer at Chipper Cash — Remote, Africa-based preferred",
    domain: "chippercash.com",
    points: 88,
    author: "chipperhiring",
    time: "18 hours ago",
    comments: 14,
    category: "job",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
      <SiteHeader />

      <main className="mx-auto max-w-[120rem] px-6 pb-20 pt-8 sm:px-10">
        <div className="mx-auto max-w-[110rem]">
          <section className="pb-4">
            <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.32em] text-[var(--color-text-dim)]">
              The pulse of African tech — curated by the community
            </p>
          </section>

          <StatsStrip />

          <section>
            {POSTS.map((post, index) => (
              <FeedRow key={post.id} post={post} rank={index + 1} />
            ))}
          </section>

          <div className="pt-8">
            <button
              type="button"
              className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-accent)]"
            >
              more →
            </button>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
