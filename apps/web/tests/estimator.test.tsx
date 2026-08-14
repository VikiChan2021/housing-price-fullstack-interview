import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EstimatorClient } from "../components/estimator-client";

const estimate = {
  estimate_id: "79f82692-2aca-4278-ae89-8d38ee143c8c",
  property: {
    square_footage: 1550,
    bedrooms: 3,
    bathrooms: 2,
    year_built: 1997,
    lot_size: 6800,
    distance_to_city_center: 4.1,
    school_rating: 7.6,
  },
  predicted_price: 248849.64,
  model_version: "ridge-test",
  warnings: [],
  created_at: "2026-08-14T00:00:00Z",
  request_id: "a7f42f79-8081-4c1a-a845-fe1393f56696",
};

describe("EstimatorClient", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("submits all seven fields and saves the returned estimate", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(estimate), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    render(<EstimatorClient />);

    expect(screen.getAllByRole("spinbutton")).toHaveLength(7);
    await userEvent.click(screen.getByRole("button", { name: "Calculate estimate" }));

    expect((await screen.findAllByText("$248,850")).length).toBeGreaterThanOrEqual(1);
    expect(fetchMock).toHaveBeenCalledWith("/api/estimates", expect.objectContaining({ method: "POST" }));
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body));
    expect(payload).toEqual(estimate.property);
    await waitFor(() => expect(localStorage.getItem("housing-estimates:v1")).toContain(estimate.estimate_id));
  });

  it("keeps invalid input on the client and does not call the API", () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<EstimatorClient />);
    const area = screen.getByLabelText("Living area");
    fireEvent.change(area, { target: { value: "0" } });
    fireEvent.submit(area.closest("form")!);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows a retry action for a recoverable API failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: { message: "ML API is unavailable", request_id: "request-7" } }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<EstimatorClient />);
    await userEvent.click(screen.getByRole("button", { name: "Calculate estimate" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("ML API is unavailable");
    expect(screen.getByRole("button", { name: "Retry last estimate" })).toBeEnabled();
  });
});
