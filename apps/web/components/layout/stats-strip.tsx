const STATS = [
  { value: "2,847", label: "builders" },
  { value: "143", label: "posts today" },
  { value: "38", label: "countries" },
  { value: "891", label: "comments" },
];

export function StatsStrip() {
  return (
    <section className="mb-2 flex flex-wrap gap-x-16 gap-y-8 border-b border-[var(--color-border)] py-8">
      {STATS.map((stat) => (
        <div key={stat.label} className="min-w-[9rem]">
          <p className="font-display text-[length:var(--fs-stat-number)] tracking-[-0.04em] text-[var(--color-accent)]">
            {stat.value}
          </p>
          <p className="mt-2 font-mono text-[length:var(--fs-label)] tracking-[0.06em] text-[var(--color-text-dim)]">
            {stat.label}
          </p>
        </div>
      ))}
    </section>
  );
}
