export function FeedEmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <section className="rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-6 py-8">
      <h2 className="font-display text-[length:var(--fs-heading-form)] tracking-[-0.03em] text-[var(--color-text)]">
        {title}
      </h2>
      <p className="mt-3 max-w-2xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
        {message}
      </p>
    </section>
  );
}
