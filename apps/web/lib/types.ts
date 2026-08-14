export type PropertyFeatures = {
  square_footage: number;
  bedrooms: number;
  bathrooms: number;
  year_built: number;
  lot_size: number;
  distance_to_city_center: number;
  school_rating: number;
};

export type RangeWarning = {
  code: string;
  field: string;
  message: string;
};

export type Estimate = {
  estimate_id: string;
  property: PropertyFeatures;
  predicted_price: number;
  model_version: string;
  warnings: RangeWarning[];
  created_at: string;
  request_id?: string;
};

export type MarketSummary = {
  count: number;
  average_price: number | null;
  median_price: number | null;
  min_price: number | null;
  max_price: number | null;
  average_square_footage: number | null;
  applied_filters: Record<string, number>;
  cache: { hit: boolean; ttl_seconds: number };
  request_id: string;
};

export type MarketProperty = PropertyFeatures & { id: number; price: number };

export type PropertyPage = {
  items: MarketProperty[];
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
  sort: string;
  applied_filters: Record<string, number>;
  request_id: string;
};

export type SegmentResponse = {
  group_by: "bedrooms" | "year_band" | "price_band";
  segments: Array<{
    key: string;
    label: string;
    count: number;
    average_price: number;
    median_price: number;
  }>;
  applied_filters: Record<string, number>;
  request_id: string;
};

export type WhatIfResponse = {
  baseline_prediction: number;
  scenario_prediction: number;
  absolute_difference: number;
  percentage_difference: number | null;
  model_version: string;
  baseline_warnings: RangeWarning[];
  scenario_warnings: RangeWarning[];
  disclaimer: string;
  request_id: string;
};

export type MarketInitialData = {
  summary: MarketSummary;
  properties: PropertyPage;
  segments: SegmentResponse;
};
