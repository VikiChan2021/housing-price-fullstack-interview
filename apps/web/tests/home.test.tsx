import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../app/page";

describe("Home", () => {
  it("labels the portal as an implementation scaffold", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "Housing Price Portal" })).toBeTruthy();
    expect(screen.getByText(/implementation scaffold/i)).toBeTruthy();
  });
});
