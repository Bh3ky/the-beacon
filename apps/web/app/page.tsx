export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f0f9ff,transparent_40%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-6 py-24 text-slate-950">
      <div className="mx-auto flex max-w-4xl flex-col gap-6">
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-sky-700">
          Phase 1 Foundation
        </p>
        <h1 className="max-w-2xl text-5xl font-semibold tracking-tight text-balance">
          RiftHub web scaffold is running.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-slate-600">
          This app is intentionally minimal. Product routes, shared UI
          primitives, and backend integrations are deferred to later phases.
        </p>
      </div>
    </main>
  );
}
