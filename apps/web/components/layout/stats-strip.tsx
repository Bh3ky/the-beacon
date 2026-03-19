import type { ReactNode } from "react";

import { getPlatformSummary } from "@/lib/api/stats";

type StatCard = {
  value: string;
  label: string;
  trend: string;
  tone: "up" | "down" | "flat";
};

function formatWhole(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatRate(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: value < 10 ? 1 : 0,
    maximumFractionDigits: 1,
  }).format(value);
}

function formatTrend(
  delta: number | null | undefined,
  label: string,
): Pick<StatCard, "trend" | "tone"> {
  if (typeof delta !== "number" || !Number.isFinite(delta)) {
    return { trend: `new vs ${label}`, tone: "flat" };
  }
  if (delta === 0) {
    return { trend: `flat vs ${label}`, tone: "flat" };
  }
  const direction = delta > 0 ? "↑" : "↓";
  return {
    trend: `${direction} ${Math.abs(delta).toFixed(1)}% vs ${label}`,
    tone: delta > 0 ? "up" : "down",
  };
}

async function SummaryStats() {
  const summary = await getPlatformSummary();

  const stats: StatCard[] = [
    {
      value: formatWhole(summary.builders_this_month),
      label: "builders this month",
      ...formatTrend(summary.builders_delta_pct, "last month"),
    },
    {
      value: formatWhole(summary.funding_stories_last_30d),
      label: "funding stories / 30d",
      ...formatTrend(summary.funding_stories_delta_pct, "previous 30d"),
    },
    {
      value: formatRate(summary.posts_per_hour),
      label: "posts / hour",
      ...formatTrend(summary.posts_per_hour_delta_pct, "previous day"),
    },
    {
      value: formatWhole(summary.comments_this_week),
      label: "comments this week",
      ...formatTrend(summary.comments_delta_pct, "previous week"),
    },
    {
      value: formatWhole(summary.jobs_live),
      label: "jobs live",
      ...formatTrend(summary.jobs_live_delta_pct, "last week"),
    },
  ];

  return (
    <>
      {stats.map((stat) => (
        <div key={stat.label} className="min-w-[10rem]">
          <p className="font-display text-[length:var(--fs-stat-number)] tracking-[-0.04em] text-[var(--color-accent)]">
            {stat.value}
          </p>
          <p className="mt-2 font-mono text-[length:var(--fs-label)] tracking-[0.08em] text-[var(--color-text-dim)]">
            {stat.label}
          </p>
          <p
            className={[
              "mt-2 font-mono text-[length:var(--fs-meta)] tracking-[0.04em]",
              stat.tone === "up"
                ? "text-[var(--color-success)]"
                : stat.tone === "down"
                  ? "text-[var(--color-error)]"
                  : "text-[var(--color-text-faint)]",
            ].join(" ")}
          >
            {stat.trend}
          </p>
        </div>
      ))}
    </>
  );
}

function SummaryFallback() {
  const fallback: StatCard[] = [
    {
      value: "live",
      label: "backend summary offline",
      trend: "start the API for real trends",
      tone: "flat",
    },
    {
      value: "real",
      label: "stats replace hardcoded demo data",
      trend: "comparison windows come from backend data",
      tone: "flat",
    },
  ];

  return (
    <>
      {fallback.map((stat) => (
        <div key={stat.label} className="min-w-[10rem]">
          <p className="font-display text-[length:var(--fs-stat-number)] tracking-[-0.04em] text-[var(--color-accent)]">
            {stat.value}
          </p>
          <p className="mt-2 font-mono text-[length:var(--fs-label)] tracking-[0.08em] text-[var(--color-text-dim)]">
            {stat.label}
          </p>
          <p className="mt-2 font-mono text-[length:var(--fs-meta)] tracking-[0.04em] text-[var(--color-text-faint)]">
            {stat.trend}
          </p>
        </div>
      ))}
    </>
  );
}

export async function StatsStrip() {
  let content: ReactNode;

  try {
    content = await SummaryStats();
  } catch {
    content = <SummaryFallback />;
  }

  return (
    <section className="mb-2 flex flex-wrap gap-x-12 gap-y-8 border-b border-[var(--color-border)] py-8">
      {content}
    </section>
  );
}
