"use client";

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
  setCachedState: () => undefined,
});

export function MarketStateProvider({ children }: { children: ReactNode }) {
  const [cachedState, setCachedState] = useState<MarketViewState | null>(null);
  const value = useMemo(() => ({ cachedState, setCachedState }), [cachedState]);

  return <MarketStateContext.Provider value={value}>{children}</MarketStateContext.Provider>;
}

export function useMarketStateCache() {
  return useContext(MarketStateContext);
}
