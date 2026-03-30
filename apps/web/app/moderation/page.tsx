import { redirect } from "next/navigation";

import { IngestionReviewPanel } from "@/components/moderation/ingestion-review-panel";
import { ModerationDashboard } from "@/components/moderation/moderation-dashboard";
import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { getCurrentUserServer } from "@/lib/api/auth";
import { ApiFetchError } from "@/lib/api/client";
import { getIngestionReviewQueue, getIngestionSourceHealth, getModerationFlagQueue } from "@/lib/api/moderation";

export default async function ModerationPage() {
  const currentUser = await getCurrentUserServer();

  if (currentUser === null) {
    redirect("/login");
  }

  if (currentUser.role !== "moderator" && currentUser.role !== "admin") {
    redirect("/");
  }

  try {
    const [queue, ingestionQueue, sourceHealth] = await Promise.all([
      getModerationFlagQueue(),
      getIngestionReviewQueue(),
      getIngestionSourceHealth(),
    ]);

    return (
      <AppShell>
        <SiteHeader activeTab={null} />

        <main className="flex-1 px-6 pb-20 pt-8 sm:px-10">
          <div className="mx-auto max-w-344">
            <ModerationDashboard initialItems={queue.items} currentUser={currentUser} />
            <IngestionReviewPanel
              initialItems={ingestionQueue.items}
              initialSourceHealth={sourceHealth.items}
              currentUser={currentUser}
            />
          </div>
        </main>

        <SiteFooter />
      </AppShell>
    );
  } catch (error) {
    if (error instanceof ApiFetchError && error.status === 403) {
      redirect("/");
    }
    throw error;
  }
}
