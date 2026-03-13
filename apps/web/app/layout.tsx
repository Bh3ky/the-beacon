import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RiftHub",
  description: "Phase 1 scaffold for the RiftHub web app.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
