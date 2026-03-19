import { AuthShell } from "@/components/auth/auth-shell";
import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <AuthShell
      activeTab="register"
      heading="Join RiftHub"
      subheading="Create an account and join the conversation shaping African tech."
    >
      <RegisterForm />
    </AuthShell>
  );
}
