const CATEGORY_STYLES = {
  funding: "bg-[var(--badge-funding-bg)] text-[var(--badge-funding-text)]",
  show: "bg-[var(--badge-show-bg)] text-[var(--badge-show-text)]",
  ask: "bg-[var(--badge-ask-bg)] text-[var(--badge-ask-text)]",
  opinion: "bg-[var(--badge-opinion-bg)] text-[var(--badge-opinion-text)]",
  policy: "bg-[var(--badge-policy-bg)] text-[var(--badge-policy-text)]",
  news: "bg-[var(--badge-news-bg)] text-[var(--badge-news-text)]",
  job: "bg-[var(--badge-job-bg)] text-[var(--badge-job-text)]",
} as const;

const CATEGORY_LABELS = {
  funding: "funding",
  show: "show rift",
  ask: "ask rift",
  opinion: "opinion",
  policy: "policy",
  news: "news",
  job: "job",
} as const;

export type FeedCategory = keyof typeof CATEGORY_STYLES;

export function CategoryBadge({ category }: { category: FeedCategory }) {
  const classes = CATEGORY_STYLES[category];
  const label = CATEGORY_LABELS[category];

  if (category === "news") {
    return null;
  }

  return (
    <span
      className={[
        "inline-flex items-center rounded-sm px-3 py-1 text-[length:var(--fs-badge)]",
        "font-mono uppercase tracking-[0.18em]",
        classes,
      ].join(" ")}
    >
      {label}
    </span>
  );
}
