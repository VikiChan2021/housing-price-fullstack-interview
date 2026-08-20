import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../app/page";

describe("Home", () => {
  it("routes users to both implemented applications", () => {
    // Role-based queries verify accessible names as well as visible navigation content.
    render(<Home />);

    expect(screen.getByRole("heading", { name: "One portal. Two ways to understand a property." })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Property Estimator/i })).toHaveAttribute("href", "/estimator");
    expect(screen.getByRole("link", { name: /Market Analysis/i })).toHaveAttribute("href", "/market");
  });
});
