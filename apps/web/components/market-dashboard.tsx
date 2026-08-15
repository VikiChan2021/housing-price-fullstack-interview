"use client";

import { FormEvent, useMemo, useState } from "react";

import { withBasePath } from "@/lib/base-path";
import type { MarketInitialData, PropertyFeatures, WhatIfResponse } from "@/lib/types";

type Filters = { min_price: string; max_price: string; bedrooms: string; min_square_footage: string };
const emptyFilters: Filters = { min_price: "", max_price: "", bedrooms: "", min_square_footage: "" };
const propertyDefaults: PropertyFeatures = { square_footage: 1550, bedrooms: 3, bathrooms: 2, year_built: 1997, lot_size: 6800, distance_to_city_center: 4.1, school_rating: 7.6 };
const scenarioDefaults: PropertyFeatures = { ...propertyDefaults, square_footage: 1750 };
const featureFields: Array<{ key: keyof PropertyFeatures; label: string; step: number }> = [
  { key: "square_footage", label: "Living area", step: 1 },
  { key: "bedrooms", label: "Bedrooms", step: 1 },
  { key: "bathrooms", label: "Bathrooms", step: 0.5 },
  { key: "year_built", label: "Year built", step: 1 },
  { key: "lot_size", label: "Lot size", step: 1 },
  { key: "distance_to_city_center", label: "City distance", step: 0.1 },
  { key: "school_rating", label: "School rating", step: 0.1 },
];
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

function queryFor(filters: Filters): URLSearchParams {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) if (value !== "") query.set(key, value);
  return query;
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(withBasePath(path), options);
  const type = response.headers.get("content-type") ?? "";
  const payload = type.includes("json") ? await response.json() as unknown : null;
  if (!response.ok) {
    const error = payload as { error?: { message?: string; request_id?: string } } | null;
    throw new Error(`${error?.error?.message ?? `Request failed with ${response.status}`}${error?.error?.request_id ? ` Request: ${error.error.request_id}` : ""}`);
  }
  return payload as T;
}

export function MarketDashboard({ initialData }: { initialData: MarketInitialData }) {
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [summary, setSummary] = useState(initialData.summary);
  const [properties, setProperties] = useState(initialData.properties);
  const [segments, setSegments] = useState(initialData.segments);
  const [groupBy, setGroupBy] = useState<"bedrooms" | "year_band" | "price_band">("bedrooms");
  const [sort, setSort] = useState("id,asc");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [whatIf, setWhatIf] = useState<WhatIfResponse | null>(null);
  const [whatIfPending, setWhatIfPending] = useState(false);
  const [baseline, setBaseline] = useState(propertyDefaults);
  const [scenario, setScenario] = useState(scenarioDefaults);

  async function refresh(
    nextPage = 0,
    nextSort = sort,
    nextGroup = groupBy,
    activeFilters = filters,
  ) {
    setPending(true);
    setError(null);
    const query = queryFor(activeFilters);
    const summaryQuery = query.toString();
    const propertiesQuery = new URLSearchParams(query);
    propertiesQuery.set("page", String(nextPage));
    propertiesQuery.set("size", "10");
    propertiesQuery.set("sort", nextSort);
    const segmentQuery = new URLSearchParams(query);
    segmentQuery.set("group_by", nextGroup);
    try {
      const [nextSummary, nextProperties, nextSegments] = await Promise.all([
        api<MarketInitialData["summary"]>(`/api/market/summary${summaryQuery ? `?${summaryQuery}` : ""}`),
        api<MarketInitialData["properties"]>(`/api/market/properties?${propertiesQuery}`),
        api<MarketInitialData["segments"]>(`/api/market/segments?${segmentQuery}`),
      ]);
      setSummary(nextSummary);
      setProperties(nextProperties);
      setSegments(nextSegments);
      setSort(nextSort);
      setGroupBy(nextGroup);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Market data could not be refreshed.");
    } finally {
      setPending(false);
    }
  }

  function applyFilters(event: FormEvent) {
    event.preventDefault();
    void refresh(0);
  }

  function updateScenario(which: "baseline" | "scenario", key: keyof PropertyFeatures, value: string) {
    const setter = which === "baseline" ? setBaseline : setScenario;
    setter((current) => ({ ...current, [key]: Number(value) }));
  }

  async function submitWhatIf(event: FormEvent) {
    event.preventDefault();
    setWhatIfPending(true);
    setError(null);
    try {
      const result = await api<WhatIfResponse>("/api/market/what-if", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseline, scenario }),
      });
      setWhatIf(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "What-if analysis failed.");
    } finally {
      setWhatIfPending(false);
    }
  }

  const exportQuery = useMemo(() => queryFor(filters).toString(), [filters]);
  const segmentMax = Math.max(...segments.segments.map((item) => item.average_price), 1);
  const metrics = [
    ["Matching homes", String(summary.count)],
    ["Average price", summary.average_price == null ? "—" : money.format(summary.average_price)],
    ["Median price", summary.median_price == null ? "—" : money.format(summary.median_price)],
    ["Average area", summary.average_square_footage == null ? "—" : `${number.format(summary.average_square_footage)} sq ft`],
  ];

  return (
    <div className="stack">
      <section className="panel" aria-labelledby="filters-title">
        <div className="panel-heading">
          <div><p className="eyebrow">Dataset controls</p><h2 id="filters-title">Refine the market</h2></div>
          <div className="export-links"><a href={withBasePath(`/api/market/export?format=csv${exportQuery ? `&${exportQuery}` : ""}`)}>Export CSV</a><a href={withBasePath(`/api/market/export?format=pdf${exportQuery ? `&${exportQuery}` : ""}`)}>Export PDF</a></div>
        </div>
        <form className="filter-row" onSubmit={applyFilters}>
          <div className="field"><label htmlFor="min-price">Minimum price</label><input id="min-price" type="number" min="0" placeholder="Any" value={filters.min_price} onChange={(event) => setFilters({ ...filters, min_price: event.target.value })} /></div>
          <div className="field"><label htmlFor="max-price">Maximum price</label><input id="max-price" type="number" min="0" placeholder="Any" value={filters.max_price} onChange={(event) => setFilters({ ...filters, max_price: event.target.value })} /></div>
          <div className="field"><label htmlFor="bedrooms">Bedrooms</label><select id="bedrooms" value={filters.bedrooms} onChange={(event) => setFilters({ ...filters, bedrooms: event.target.value })}><option value="">Any</option><option value="2">2</option><option value="3">3</option><option value="4">4</option></select></div>
          <div className="field"><label htmlFor="min-area">Minimum living area</label><input id="min-area" type="number" min="1" placeholder="Any" value={filters.min_square_footage} onChange={(event) => setFilters({ ...filters, min_square_footage: event.target.value })} /></div>
          <div className="actions field full"><button className="button primary" disabled={pending} type="submit">{pending ? "Refreshing…" : "Apply filters"}</button><button className="button subtle" type="button" onClick={() => { setFilters(emptyFilters); void refresh(0, sort, groupBy, emptyFilters); }}>Reset</button></div>
        </form>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="status-line"><span>{Object.keys(summary.applied_filters).length ? `${Object.keys(summary.applied_filters).length} active filter(s)` : "Showing all supplied records"}</span><span>Cache {summary.cache.hit ? "hit" : "miss"} · request {summary.request_id.slice(0, 8)}</span></div>
      </section>

      <section aria-label="Market summary" className="summary-grid" aria-live="polite">
        {metrics.map(([label, value]) => <div className="metric-card" key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </section>

      <div className="dashboard-grid">
        <section className="panel" aria-labelledby="segments-title">
          <div className="panel-heading"><div><p className="eyebrow">Visual comparison</p><h2 id="segments-title">Market segments</h2></div></div>
          <div className="field"><label htmlFor="group-by">Group properties by</label><select id="group-by" value={groupBy} onChange={(event) => void refresh(0, sort, event.target.value as typeof groupBy)}><option value="bedrooms">Bedrooms</option><option value="year_band">Year built</option><option value="price_band">Price band</option></select></div>
          {segments.segments.length === 0 ? <div className="empty-state">No segments match these filters.</div> : <div className="bar-chart" role="img" aria-label={`Average price grouped by ${segments.group_by}`}>{segments.segments.map((item) => <div className="bar-row" key={item.key}><span>{item.label}</span><div className="bar-track"><div className="bar-fill" style={{ width: `${item.average_price / segmentMax * 100}%` }} /></div><strong>{money.format(item.average_price)}</strong></div>)}</div>}
        </section>

        <section className="panel" aria-labelledby="properties-title">
          <div className="panel-heading"><div><p className="eyebrow">Source rows</p><h2 id="properties-title">Matching properties</h2></div><span className="micro">{properties.total_items} total</span></div>
          {properties.items.length === 0 ? <div className="empty-state">No properties match. Broaden or reset the filters.</div> : <div className="table-wrap"><table><thead><tr><th>ID</th><th>Area</th><th>Beds</th><th>Baths</th><th>Year</th><th>School</th><th><button className="sort-button" type="button" onClick={() => void refresh(0, sort === "price,desc" ? "price,asc" : "price,desc")}>Price {sort === "price,desc" ? "↓" : sort === "price,asc" ? "↑" : "↕"}</button></th></tr></thead><tbody>{properties.items.map((item) => <tr key={item.id}><td>{item.id}</td><td>{number.format(item.square_footage)}</td><td>{item.bedrooms}</td><td>{item.bathrooms}</td><td>{item.year_built}</td><td>{item.school_rating}</td><td>{money.format(item.price)}</td></tr>)}</tbody></table></div>}
          <div className="pagination"><button className="button subtle" disabled={pending || properties.page === 0} type="button" onClick={() => void refresh(properties.page - 1)}>Previous</button><span className="micro">Page {properties.total_pages === 0 ? 0 : properties.page + 1} of {properties.total_pages}</span><button className="button subtle" disabled={pending || properties.page + 1 >= properties.total_pages} type="button" onClick={() => void refresh(properties.page + 1)}>Next</button></div>
        </section>
      </div>

      <section className="panel" aria-labelledby="what-if-title">
        <div className="panel-heading"><div><p className="eyebrow">Model-backed scenario</p><h2 id="what-if-title">What changes when the property changes?</h2></div><span className="micro">Association, not causation</span></div>
        <form onSubmit={submitWhatIf}>
          <div className="scenario-grid">
            {(["baseline", "scenario"] as const).map((which) => {
              const values = which === "baseline" ? baseline : scenario;
              return <fieldset className="scenario-card" key={which}><legend><h3>{which === "baseline" ? "Baseline property" : "Scenario property"}</h3></legend><div className="field-grid">{featureFields.map((field) => <div className="field" key={field.key}><label htmlFor={`${which}-${field.key}`}>{field.label}</label><input id={`${which}-${field.key}`} required type="number" min={field.key === "year_built" ? 1600 : field.key === "square_footage" || field.key === "lot_size" ? 1 : 0} max={field.key === "school_rating" ? 10 : field.key === "year_built" ? 2100 : undefined} step={field.step} value={values[field.key]} onChange={(event) => updateScenario(which, field.key, event.target.value)} /></div>)}</div></fieldset>;
            })}
          </div>
          <div className="actions"><button className="button primary" disabled={whatIfPending} type="submit">{whatIfPending ? "Comparing…" : "Compare scenarios"}</button></div>
        </form>
        {whatIf && <div aria-live="polite"><div className="result-delta"><div><span>Baseline</span><strong>{money.format(whatIf.baseline_prediction)}</strong></div><div><span>Scenario</span><strong>{money.format(whatIf.scenario_prediction)}</strong></div><div><span>Difference</span><strong>{money.format(whatIf.absolute_difference)} ({whatIf.percentage_difference ?? "—"}%)</strong></div></div><p className="micro">{whatIf.disclaimer} · model {whatIf.model_version}</p></div>}
      </section>
    </div>
  );
}
