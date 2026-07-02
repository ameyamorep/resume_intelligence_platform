import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resume Intelligence Platform",
  description: "AI-powered resume analysis against any job description",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
