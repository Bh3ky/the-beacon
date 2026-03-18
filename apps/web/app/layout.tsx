import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RiftHub",
  description: "Community-ranked discovery and discussion platform for African tech.",
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
