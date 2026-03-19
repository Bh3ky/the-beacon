import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { SubmitForm } from "@/components/submit/submit-form";

export default function SubmitPage() {
  return (
    <AppShell>
      <SiteHeader activeTab={null} />

      <main className="flex-1 px-6 pb-20 pt-8 sm:px-10">
        <div className="mx-auto max-w-[72rem]">
          <section className="border-b border-[var(--color-border)] pb-6">
            <p className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.32em] text-[var(--color-text-dim)]">
              Submit to the feed
            </p>
            <h1 className="mt-5 font-display text-[length:var(--fs-heading-form)] tracking-[-0.04em] text-[var(--color-text)]">
              Ship a link, a text post, or a live job.
            </h1>
            <p className="mt-3 max-w-3xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
              This surface talks to the real Phase 3 API through the frontend proxy so
              browser cookies and CSRF stay on the same origin.
            </p>
          </section>

          <section className="pt-10">
            <SubmitForm />
          </section>
        </div>
      </main>

      <SiteFooter />
    </AppShell>
  );
}
