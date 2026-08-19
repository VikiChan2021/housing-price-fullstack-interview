import Link from "next/link";

export default function Home() {
  return (
    <main id="main-content" className="page-shell home-hero">
      <p className="eyebrow">Housing intelligence, explained</p>
      <h1>One portal. Two ways to understand a property.</h1>
      <p className="hero-copy">
        Estimate an individual home with the trained model, or explore the supplied market dataset
        through transparent statistics, filters, and model-backed scenarios.
      </p>
      <div className="home-grid">
        <Link className="feature-card" href="/estimator">
          <span className="card-index">01</span>
          <h2>Property Estimator</h2>
          <p>Enter seven property facts, receive a model estimate, and compare saved scenarios.</p>
          <span className="text-link">Open estimator →</span>
        </Link>
        <Link className="feature-card warm" href="/market">
          <span className="card-index">02</span>
          <h2>Market Analysis</h2>
          <p>Filter all 50 records, inspect matching properties, run what-if analysis, and export evidence.</p>
          <span className="text-link">Open market dashboard →</span>
        </Link>
      </div>
      <p className="data-note">Built from the provided 50-row interview dataset. No hidden external market data.</p>
    </main>
  );
}
