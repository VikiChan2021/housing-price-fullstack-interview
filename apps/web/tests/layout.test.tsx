import { describe, expect, it } from "vitest";

import RootLayout from "../app/layout";

describe("RootLayout", () => {
  it("keeps document hydration tolerant of extension-injected root attributes", () => {
    // Direct invocation inspects the root React element without requiring a full Next.js runtime.
    const layout = RootLayout({ children: <main /> });

    expect(layout.type).toBe("html");
    expect(layout.props.suppressHydrationWarning).toBe(true);
    expect(layout.props["data-scroll-behavior"]).toBe("smooth");
  });
});
