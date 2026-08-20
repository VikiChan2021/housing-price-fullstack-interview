/** Provide an accessible route-level fallback while async Server Components resolve. */
export default function Loading() {
  return (
    <main id="main-content" className="page-shell" aria-busy="true" aria-live="polite">
      <p className="eyebrow">Loading</p>
      <div className="skeleton skeleton-title" />
      <div className="skeleton-grid">
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    </main>
  );
}
