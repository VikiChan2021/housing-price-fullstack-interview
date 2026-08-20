"use client";

// This client boundary retains dashboard state while users navigate within the shared layout.

import {
  createContext,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useContext,
  useMemo,
  useState,
} from "react";

import type {
  MarketSummary,
  PropertyFeatures,
  PropertyPage,
  WhatIfResponse,
} from "@/lib/types";

export type MarketFilters = {
  min_price: string;
  max_price: string;
  bedrooms: string;
  min_square_footage: string;
};

export type MarketViewState = {
  filters: MarketFilters;
  summary: MarketSummary;
  properties: PropertyPage;
  sort: string;
  baseline: PropertyFeatures;
  scenario: PropertyFeatures;
  whatIf: WhatIfResponse | null;
};

type MarketStateContextValue = {
  cachedState: MarketViewState | null;
  setCachedState: Dispatch<SetStateAction<MarketViewState | null>>;
};

const MarketStateContext = createContext<MarketStateContextValue>({
  cachedState: null,
  // The no-op default keeps isolated consumers safe; the layout installs the real provider.
  setCachedState: () => undefined,
});

export function MarketStateProvider({ children }: { children: ReactNode }) {
  const [cachedState, setCachedState] = useState<MarketViewState | null>(null);
  // Memoization avoids notifying consumers when neither context field has changed.
  const value = useMemo(() => ({ cachedState, setCachedState }), [cachedState]);

  return <MarketStateContext.Provider value={value}>{children}</MarketStateContext.Provider>;
}

export function useMarketStateCache() {
  return useContext(MarketStateContext);
}
