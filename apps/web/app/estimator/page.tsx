import { EstimatorClient } from "@/components/estimator-client";

export const metadata = { title: "Property Estimator | Hearth & Metric" };

/** Keep static page framing on the server and delegate only interactive behavior to the client. */
export default function EstimatorPage() {
  return (
    <main id="main-content" className="page-shell">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Property estimator</p>
          <h1>Turn property facts into a clear estimate.</h1>
        </div>
        <p>
          Enter the seven features used by the trained Ridge model. Results stay in this browser so
          you can compare scenarios without creating an account.
        </p>
      </div>
      <EstimatorClient />
    </main>
  );
}
