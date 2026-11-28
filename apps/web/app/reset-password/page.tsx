import { AuthShell } from "@/components/auth/auth-shell";
import { ResetPasswordForm } from "@/components/auth/reset-password-form";

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams?: Promise<{ token?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  return (
    <AuthShell activeTab="login" heading="Choose a new password">
      <ResetPasswordForm token={resolvedSearchParams?.token} />
    </AuthShell>
  );
}
