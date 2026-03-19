export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col overflow-hidden border-x border-(--color-border-strong) bg-(--color-surface) shadow-[0_30px_120px_rgba(0,0,0,0.45)] ring-1 ring-[rgba(240,235,227,0.03)]">
        {children}
      </div>
    </div>
  );
}
