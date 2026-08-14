"use client";

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
