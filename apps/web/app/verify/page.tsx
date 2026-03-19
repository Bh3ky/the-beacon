import { AuthShell } from "@/components/auth/auth-shell";
import { VerifyForm } from "@/components/auth/verify-form";

export default async function VerifyPage({
  searchParams,
}: {
  searchParams?: Promise<{ token?: string; next?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  return (
    <AuthShell
      activeTab="login"
      heading="Verify your account"
      subheading="Open the link from your inbox or paste the token here to activate your account and start your browser session."
    >
      <VerifyForm
        initialToken={resolvedSearchParams?.token}
        nextHref={resolvedSearchParams?.next}
      />
    </AuthShell>
  );
}
