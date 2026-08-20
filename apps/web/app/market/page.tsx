import { MarketDashboard } from "@/components/market-dashboard";
import { getInitialMarketData } from "@/lib/market-server";

// Market data must be requested per visit rather than captured in a static build artifact.
export const dynamic = "force-dynamic";
export const metadata = { title: "Market Analysis | Hearth & Metric" };

export default async function MarketPage() {
  // Fetch before rendering so the first HTML already contains source-backed market evidence.
  const initialData = await getInitialMarketData();
  return (
    <main id="main-content" className="page-shell">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Market analysis</p>
          <h1>See the shape behind the asking price.</h1>
        </div>
        <p>
          This first view was loaded on the server. Refine the supplied dataset, inspect comparable
          properties, and test model-backed scenarios without treating association as causation.
        </p>
      </div>
      <MarketDashboard initialData={initialData} />
    </main>
  );
}
