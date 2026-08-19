import { MarketDashboard } from "@/components/market-dashboard";
import { getInitialMarketData } from "@/lib/market-server";

export const dynamic = "force-dynamic";
export const metadata = { title: "Market Analysis | Hearth & Metric" };

export default async function MarketPage() {
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
