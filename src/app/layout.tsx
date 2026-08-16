import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "$GROWTH · Autonomous Marketing Growth Hacker",
  description:
    "B2B dashboard for autonomous liquidity balancing, spread protection, and agent treasury management.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
