import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MarketDashboard } from "../components/market-dashboard";
import { MarketStateProvider } from "../components/market-state-provider";
import type { MarketInitialData } from "../lib/types";

const initial: MarketInitialData = {
  summary: { count: 50, average_price: 264600, median_price: 245000, min_price: 160000, max_price: 410000, average_square_footage: 1690.2, applied_filters: {}, cache: { hit: false, ttl_seconds: 300 }, request_id: "summary-request" },
  properties: { items: [{ id: 1, square_footage: 1250, bedrooms: 2, bathrooms: 1, year_built: 1985, lot_size: 5000, distance_to_city_center: 3.2, school_rating: 7.5, price: 180000 }], page: 0, size: 10, total_items: 50, total_pages: 5, sort: "id,asc", applied_filters: {}, request_id: "page-request" },
};

function json(payload: unknown) {
  // Keep test responses faithful to the JSON content-type branch in the production fetch helper.
  return new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } });
}

describe("MarketDashboard", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("renders the server summary and a full-width source table", () => {
    render(<MarketDashboard initialData={initial} />);
    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.getByText("$264,600")).toBeInTheDocument();
    expect(screen.queryByText("Market segments")).not.toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Lot" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Distance" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "$180,000" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search properties" })).toBeInTheDocument();
    expect(screen.queryByText(/Cache (hit|miss)/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Export PDF" }).getAttribute("href"))
      .toContain("time_zone=");
  });

  it("refreshes summary and rows with the same filters", async () => {
    const filteredSummary = { ...initial.summary, count: 22, average_price: 240909.09, applied_filters: { bedrooms: 3 }, cache: { hit: true, ttl_seconds: 300 } };
    const filteredPage = { ...initial.properties, total_items: 22, items: [{ ...initial.properties.items[0], id: 2, bedrooms: 3, price: 265000 }] };
    // Route summary and property requests to distinct fixtures while recording both URLs.
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("summary")) return json(filteredSummary);
      return json(filteredPage);
    });
    render(<MarketDashboard initialData={initial} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Bedrooms" }), "3");
    await userEvent.click(screen.getByRole("button", { name: "Search properties" }));

    expect(await screen.findByText("22")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const [url] of fetchMock.mock.calls) expect(String(url)).toContain("bedrooms=3");
  });

  it("restores filters and filtered rows after navigating away and back", async () => {
    const filteredSummary = { ...initial.summary, count: 22, applied_filters: { bedrooms: 3 } };
    const filteredPage = { ...initial.properties, total_items: 22, items: [{ ...initial.properties.items[0], bedrooms: 3 }] };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).includes("summary") ? json(filteredSummary) : json(filteredPage));

    function RouteHarness() {
      // Unmount and remount the dashboard while keeping its layout-level provider alive.
      const [showMarket, setShowMarket] = useState(true);
      return (
        <MarketStateProvider>
          <button type="button" onClick={() => setShowMarket((current) => !current)}>
            Switch route
          </button>
          {showMarket ? <MarketDashboard initialData={initial} /> : <p>Estimator route</p>}
        </MarketStateProvider>
      );
    }

    render(<RouteHarness />);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Bedrooms" }), "3");
    await userEvent.click(screen.getByRole("button", { name: "Search properties" }));
    expect(await screen.findByText("22")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Switch route" }));
    await userEvent.click(screen.getByRole("button", { name: "Switch route" }));

    expect(screen.getByRole("combobox", { name: "Bedrooms" })).toHaveValue("3");
    expect(screen.getByText("22")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("runs the model-backed what-if comparison", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ baseline_prediction: 248849.64, scenario_prediction: 238089.19, absolute_difference: -10760.45, percentage_difference: -4.32, model_version: "ridge-test", baseline_warnings: [], scenario_warnings: [], disclaimer: "Association, not causation.", request_id: "what-if-request" }));
    render(<MarketDashboard initialData={initial} />);

    await userEvent.click(screen.getByRole("button", { name: "Compare scenarios" }));
    expect(await screen.findByText("$248,850")).toBeInTheDocument();
    expect(screen.getByText("Association, not causation.", { exact: false })).toBeInTheDocument();
  });
});
