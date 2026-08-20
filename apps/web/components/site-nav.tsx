"use client";

// Active-route styling requires the browser pathname, so this small component owns the client boundary.

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/estimator", label: "Property Estimator" },
  { href: "/market", label: "Market Analysis" },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary navigation" className="site-nav">
      {links.map((link) => {
        // startsWith also marks descendants such as /market/... as part of the Market section.
        const active = pathname.startsWith(link.href);
        return (
          <Link key={link.href} href={link.href} aria-current={active ? "page" : undefined}>
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
