import { AuthShell } from "@/components/auth/auth-shell";
import { LoginForm } from "@/components/auth/login-form";

export default async function LoginPage({
  searchParams,
}: {
  searchParams?: Promise<{ next?: string; email?: string }>;
}) {
  const resolvedSearchParams = await searchParams;

  return (
    <AuthShell
      activeTab="login"
      heading="Welcome back"
      subheading="Sign in to vote, comment, submit posts, and keep your place in the feed."
    >
      <LoginForm
        nextHref={resolvedSearchParams?.next}
        registeredEmail={resolvedSearchParams?.email}
      />
    </AuthShell>
  );
}
