import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
    // Browser persistence and fetch mocks must not cross test boundaries.
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("submits all seven fields and saves the returned estimate", async () => {
    // Mock only the network boundary while exercising real form and storage behavior.
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

  it("explains each training-range warning with its field, value, and range", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        ...estimate,
        warnings: [
          { code: "OUTSIDE_TRAINING_RANGE", field: "bathrooms", message: "Value is outside the range observed during training.", value: 9, training_min: 1, training_max: 3 },
          { code: "OUTSIDE_TRAINING_RANGE", field: "school_rating", message: "Value is outside the range observed during training.", value: 10, training_min: 6.5, training_max: 9.1 },
        ],
      }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    render(<EstimatorClient />);

    await userEvent.click(screen.getByRole("button", { name: "Calculate estimate" }));

    expect(await screen.findByText("Check these unusual inputs")).toBeInTheDocument();
    expect(screen.getByText("Bathrooms is 9, above the training-data range of 1–3. This estimate may be less reliable.")).toBeInTheDocument();
    expect(screen.getByText("School rating is 10, above the training-data range of 6.5–9.1. This estimate may be less reliable.")).toBeInTheDocument();
    expect(screen.queryByText("Value is outside the range observed during training.")).not.toBeInTheDocument();
  });

  it("migrates saved history to stable record numbers and uses the same newest-first order", async () => {
    // Seed a legacy envelope without sequence fields to exercise the in-place migration path.
    const older = { ...estimate, estimate_id: "older-estimate", predicted_price: 220000, created_at: "2026-08-14T00:00:01Z" };
    const newer = { ...estimate, estimate_id: "newer-estimate", predicted_price: 260000, created_at: "2026-08-14T00:00:02Z" };
    localStorage.setItem("housing-estimates:v1", JSON.stringify({ version: 1, estimates: [newer, older] }));

    render(<EstimatorClient />);

    const chart = await screen.findByRole("list", { name: "Recent estimate values, newest first" });
    const chartRows = within(chart).getAllByRole("listitem");
    expect(chartRows[0]).toHaveTextContent("Estimate #2");
    expect(chartRows[0]).toHaveTextContent("Newest");
    expect(chartRows[1]).toHaveTextContent("Estimate #1");

    const historyTable = screen.getByRole("table", { name: "Saved estimates, newest first" });
    const historyRows = within(historyTable).getAllByRole("row").slice(1);
    expect(historyRows[0]).toHaveTextContent("Estimate #2");
    expect(historyRows[0]).toHaveTextContent("Newest");
    expect(historyRows[0]).toHaveTextContent(/:\d{2}:\d{2}/);
    expect(historyRows[1]).toHaveTextContent("Estimate #1");
    await waitFor(() => expect(localStorage.getItem("housing-estimates:v1")).toContain('"sequence":2'));
  });
});
