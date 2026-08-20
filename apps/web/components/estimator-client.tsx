"use client";

// Form interaction and versioned localStorage history require a browser-side component.

import { FormEvent, useEffect, useMemo, useState } from "react";

import { withBasePath } from "@/lib/base-path";
import type { Estimate, PropertyFeatures, RangeWarning } from "@/lib/types";

type SavedEstimate = Estimate & { sequence: number };
// Legacy version-one entries may not yet contain the stable display sequence.
type StoredEstimate = Estimate & { sequence?: number };

// Version the storage key so future incompatible schemas can migrate without guessing.
const historyKey = "housing-estimates:v1";
const defaults: PropertyFeatures = {
  square_footage: 1550,
  bedrooms: 3,
  bathrooms: 2,
  year_built: 1997,
  lot_size: 6800,
  distance_to_city_center: 4.1,
  school_rating: 7.6,
};

const fields: Array<{
  key: keyof PropertyFeatures;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
}> = [
  { key: "square_footage", label: "Living area", unit: "sq ft", min: 1, max: 100000, step: 1 },
  { key: "bedrooms", label: "Bedrooms", unit: "rooms", min: 0, max: 100, step: 1 },
  { key: "bathrooms", label: "Bathrooms", unit: "rooms", min: 0, max: 100, step: 0.5 },
  { key: "year_built", label: "Year built", unit: "year", min: 1600, max: 2100, step: 1 },
  { key: "lot_size", label: "Lot size", unit: "sq ft", min: 1, max: 100000000, step: 1 },
  { key: "distance_to_city_center", label: "Distance to city center", unit: "miles", min: 0, max: 10000, step: 0.1 },
  { key: "school_rating", label: "School rating", unit: "0–10", min: 0, max: 10, step: 0.1 },
];

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const featureNumber = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const createdAt = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

function normalizeHistory(estimates: StoredEstimate[]): SavedEstimate[] {
  // Existing positive sequences are authoritative and must survive reloads unchanged.
  if (estimates.every((item) => Number.isInteger(item.sequence) && Number(item.sequence) > 0)) {
    return estimates as SavedEstimate[];
  }
  // History is newest-first; reverse a copy so the oldest record receives sequence one.
  const sequences = new Map(estimates.slice().reverse().map((item, index) => [item.estimate_id, index + 1]));
  return estimates.map((item) => ({ ...item, sequence: sequences.get(item.estimate_id)! }));
}

function formatCreatedAt(value: string): string {
  return createdAt.format(new Date(value));
}

function formatProperty(item: SavedEstimate): string {
  return `${featureNumber.format(item.property.square_footage)} sq ft · ${item.property.bedrooms} bd · ${featureNumber.format(item.property.bathrooms)} ba · ${item.property.year_built}`;
}

function formatWarning(warning: RangeWarning): string {
  const field = fields.find((item) => item.key === warning.field);
  const label = field?.label ?? warning.field.replaceAll("_", " ");
  const direction = warning.value < warning.training_min ? "below" : "above";
  return `${label} is ${featureNumber.format(warning.value)}, ${direction} the training-data range of ${featureNumber.format(warning.training_min)}–${featureNumber.format(warning.training_max)}. This estimate may be less reliable.`;
}

function parseError(payload: unknown): string {
  // Narrow unknown JSON defensively before reading the shared backend error envelope.
  if (payload && typeof payload === "object" && "error" in payload) {
    const error = (payload as { error?: { message?: string; request_id?: string } }).error;
    if (error?.message) return `${error.message}${error.request_id ? ` Request: ${error.request_id}` : ""}`;
  }
  return "The estimate could not be completed. Please retry.";
}

export function EstimatorClient() {
  const [history, setHistory] = useState<SavedEstimate[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<PropertyFeatures | null>(null);

  useEffect(() => {
    // Browser storage is untrusted: extensions, users, or older builds can leave invalid JSON.
    try {
      const stored = localStorage.getItem(historyKey);
      if (!stored) return;
      const envelope = JSON.parse(stored) as { version?: number; estimates?: StoredEstimate[] };
      if (envelope.version === 1 && Array.isArray(envelope.estimates)) {
        const restored = normalizeHistory(envelope.estimates.slice(0, 20));
        // Defer state restoration beyond the effect body and persist any legacy migration.
        queueMicrotask(() => {
          setHistory(restored);
          localStorage.setItem(historyKey, JSON.stringify({ version: 1, estimates: restored }));
        });
      }
    } catch {
      // A corrupt envelope is unrecoverable but must not prevent the estimator from loading.
      localStorage.removeItem(historyKey);
    }
  }, []);

  function save(next: SavedEstimate[]) {
    // Bound browser storage and UI work to the newest 20 estimates.
    const limited = next.slice(0, 20);
    setHistory(limited);
    localStorage.setItem(historyKey, JSON.stringify({ version: 1, estimates: limited }));
  }

  async function requestEstimate(payload: PropertyFeatures) {
    setPending(true);
    setError(null);
    setLastPayload(payload);
    try {
      const response = await fetch(withBasePath("/api/estimates"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = (await response.json()) as unknown;
      if (!response.ok) throw new Error(parseError(body));
      const estimate = body as Estimate;
      // Sequence numbers are local display identities and do not depend on current array position.
      const savedEstimate: SavedEstimate = {
        ...estimate,
        sequence: Math.max(0, ...history.map((item) => item.sequence)) + 1,
      };
      save([savedEstimate, ...history.filter((item) => item.estimate_id !== estimate.estimate_id)]);
      setSelected((current) => [estimate.estimate_id, ...current].slice(0, 3));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The estimate could not be completed.");
    } finally {
      setPending(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Native constraints provide immediate UX, while the server still performs authoritative checks.
    if (!event.currentTarget.reportValidity()) return;
    const data = new FormData(event.currentTarget);
    // Object.fromEntries maps the declarative field registry into the shared API payload shape.
    const payload = Object.fromEntries(fields.map((field) => [field.key, Number(data.get(field.key))])) as PropertyFeatures;
    void requestEstimate(payload);
  }

  function toggleCompare(id: string) {
    setSelected((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      // Comparison is intentionally capped at three columns to remain readable on small screens.
      if (current.length >= 3) return current;
      return [...current, id];
    });
  }

  function clearHistory() {
    save([]);
    setSelected([]);
  }

  const comparison = history.filter((item) => selected.includes(item.estimate_id));
  // The compact chart visualizes only recent records while the table retains all saved history.
  const chart = useMemo(() => history.slice(0, 6), [history]);
  const chartMax = Math.max(...chart.map((item) => item.predicted_price), 1);
  const latest = history[0];

  return (
    <div className="dashboard-grid">
      <section className="panel" aria-labelledby="estimate-form-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Seven model inputs</p>
            <h2 id="estimate-form-title">Describe the property</h2>
          </div>
        </div>
        <form onSubmit={submit} noValidate={false}>
          <div className="field-grid">
            {fields.map((field) => (
              <div className="field" key={field.key}>
                <label htmlFor={`estimate-${field.key}`}>{field.label}</label>
                <input
                  id={`estimate-${field.key}`}
                  name={field.key}
                  type="number"
                  required
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  defaultValue={defaults[field.key]}
                  aria-describedby={`estimate-${field.key}-help`}
                />
                <small id={`estimate-${field.key}-help`}>{field.unit} · {field.min} to {field.max}</small>
              </div>
            ))}
          </div>
          <div className="actions">
            <button className="button primary" disabled={pending} type="submit">
              {pending ? "Estimating…" : "Calculate estimate"}
            </button>
            <span className="micro">Server validation runs even after browser checks.</span>
          </div>
        </form>
        {error && (
          <div className="status-panel error-panel" role="alert">
            <strong>Estimate unavailable</strong>
            <p>{error}</p>
            <button className="button" disabled={pending || !lastPayload} type="button" onClick={() => lastPayload && void requestEstimate(lastPayload)}>
              Retry last estimate
            </button>
          </div>
        )}
      </section>

      <div className="stack">
        <section className="panel" aria-labelledby="latest-title" aria-live="polite">
          <div className="panel-heading">
            <h2 id="latest-title">Latest estimate</h2>
            {latest && <span className="micro">Model {latest.model_version}</span>}
          </div>
          {latest ? (
            <>
              <div className="price-hero">
                <div><span>Predicted property value</span><strong>{money.format(latest.predicted_price)}</strong></div>
                <span>Estimate #{latest.sequence} · {formatCreatedAt(latest.created_at)}</span>
              </div>
              <div className="table-wrap" style={{ marginTop: "1rem" }}>
                <table>
                  <caption className="sr-only">Latest property inputs and prediction</caption>
                  <thead><tr><th>Area</th><th>Beds</th><th>Baths</th><th>Year</th><th>Lot</th><th>Distance</th><th>School</th><th>Estimate</th></tr></thead>
                  <tbody><tr><td>{latest.property.square_footage}</td><td>{latest.property.bedrooms}</td><td>{latest.property.bathrooms}</td><td>{latest.property.year_built}</td><td>{latest.property.lot_size}</td><td>{latest.property.distance_to_city_center}</td><td>{latest.property.school_rating}</td><td>{money.format(latest.predicted_price)}</td></tr></tbody>
                </table>
              </div>
              {latest.warnings.length > 0 && <div className="reliability-notice" role="status"><strong>Check these unusual inputs</strong><p>They are outside the values represented in the training data.</p><ul>{latest.warnings.map((warning) => <li key={warning.field}>{formatWarning(warning)}</li>)}</ul></div>}
            </>
          ) : <div className="empty-state">Submit the form to create your first estimate.</div>}
        </section>

        <section className="panel" aria-labelledby="history-title">
          <div className="panel-heading">
            <div><h2 id="history-title">Saved estimates</h2><span className="micro">Stored only in this browser · choose 2–3 to compare</span></div>
            <button className="button danger" type="button" disabled={history.length === 0} onClick={clearHistory}>Clear history</button>
          </div>
          {history.length === 0 ? <div className="empty-state">No saved estimates yet.</div> : (
            <>
              <ol className="history-chart" aria-label="Recent estimate values, newest first">
                {chart.map((item, index) => <li className={`history-chart-row${index === 0 ? " is-latest" : ""}`} key={item.estimate_id}><div className="history-chart-label"><span className="history-sequence">Estimate #{item.sequence}</span>{index === 0 && <span className="newest-badge">Newest</span>}<span>{featureNumber.format(item.property.square_footage)} sq ft · {item.property.bedrooms} bd</span></div><div className="bar-track"><div className="bar-fill" style={{ width: `${item.predicted_price / chartMax * 100}%` }} /></div><strong>{money.format(item.predicted_price)}</strong></li>)}
              </ol>
              <div className="table-wrap" style={{ marginTop: "1.25rem" }}>
                <table>
                  <caption className="sr-only">Saved estimates, newest first</caption>
                  <thead><tr><th>Compare</th><th>Record</th><th>Created</th><th>Property</th><th>Estimate</th></tr></thead>
                  <tbody>{history.map((item, index) => <tr className={index === 0 ? "history-latest-row" : undefined} key={item.estimate_id}><td><label className="checkbox-label"><input type="checkbox" checked={selected.includes(item.estimate_id)} disabled={!selected.includes(item.estimate_id) && selected.length >= 3} onChange={() => toggleCompare(item.estimate_id)} /><span className="sr-only">Compare estimate {item.sequence}</span></label></td><td><span className="history-sequence">Estimate #{item.sequence}</span>{index === 0 && <span className="newest-badge">Newest</span>}</td><td><time dateTime={item.created_at}>{formatCreatedAt(item.created_at)}</time></td><td>{formatProperty(item)}</td><td>{money.format(item.predicted_price)}</td></tr>)}</tbody>
                </table>
              </div>
            </>
          )}
          {comparison.length >= 2 && (
            <div className="compare-box">
              <h3>Side-by-side comparison</h3>
              <div className="table-wrap"><table><thead><tr><th>Property</th>{comparison.map((item) => <th key={item.estimate_id}>Estimate #{item.sequence}</th>)}</tr></thead><tbody>{fields.map((field) => <tr key={field.key}><th>{field.label}</th>{comparison.map((item) => <td key={item.estimate_id}>{item.property[field.key]}</td>)}</tr>)}<tr><th>Predicted price</th>{comparison.map((item) => <td key={item.estimate_id}><strong>{money.format(item.predicted_price)}</strong></td>)}</tr></tbody></table></div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
