import { AuthShell } from "@/components/auth/auth-shell";
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      activeTab="login"
      heading="Forgot your password?"
      subheading="Enter your account email to get a reset link."
    >
      <ForgotPasswordForm />
    </AuthShell>
  );
}
