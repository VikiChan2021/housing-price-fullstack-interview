"use client";

// Error boundaries need a client reset callback to retry the failed route segment in place.
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main id="main-content" className="page-shell">
      <section className="status-panel error-panel" role="alert">
        <p className="eyebrow">Service interruption</p>
        <h1>We could not load this view.</h1>
        <p>The service may still be starting. Your input has not been submitted.</p>
        <button className="button primary" type="button" onClick={reset}>Try again</button>
      </section>
    </main>
  );
}
