import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { SiteNav } from "@/components/site-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: "Housing Price Portal",
  description: "Housing price full-stack interview project",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <header className="site-header">
          <div className="header-inner">
            <Link className="brand" href="/">Hearth &amp; Metric</Link>
            <SiteNav />
          </div>
        </header>
        {children}
        <footer className="site-footer">
          Demo estimates are model associations, not appraisals or financial advice.
        </footer>
      </body>
    </html>
  );
}
