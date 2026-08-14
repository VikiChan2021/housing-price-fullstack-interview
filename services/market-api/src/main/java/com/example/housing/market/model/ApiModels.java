package com.example.housing.market.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public final class ApiModels {
    private ApiModels() {
    }

    public record CacheInfo(boolean hit, @JsonProperty("ttl_seconds") long ttlSeconds) {
    }

    public record MarketSummary(
            long count,
            @JsonProperty("average_price") Double averagePrice,
            @JsonProperty("median_price") Double medianPrice,
            @JsonProperty("min_price") Double minPrice,
            @JsonProperty("max_price") Double maxPrice,
            @JsonProperty("average_square_footage") Double averageSquareFootage,
            @JsonProperty("applied_filters") Map<String, Number> appliedFilters,
            CacheInfo cache,
            @JsonProperty("request_id") String requestId) {
    }

    public record PropertyPage(
            List<MarketProperty> items,
            int page,
            int size,
            @JsonProperty("total_items") long totalItems,
            @JsonProperty("total_pages") int totalPages,
            String sort,
            @JsonProperty("applied_filters") Map<String, Number> appliedFilters,
            @JsonProperty("request_id") String requestId) {
    }

    public record Segment(String key, String label, long count,
                          @JsonProperty("average_price") double averagePrice,
                          @JsonProperty("median_price") double medianPrice) {
    }

    public record SegmentResponse(
            @JsonProperty("group_by") String groupBy,
            List<Segment> segments,
            @JsonProperty("applied_filters") Map<String, Number> appliedFilters,
            @JsonProperty("request_id") String requestId) {
    }

    public record WhatIfRequest(@NotNull @Valid PropertyFeatures baseline,
                                @NotNull @Valid PropertyFeatures scenario) {
    }

    public record RangeWarning(String code, String field, String message, double value,
                               @JsonProperty("training_min") double trainingMin,
                               @JsonProperty("training_max") double trainingMax) {
    }

    public record WhatIfResponse(
            @JsonProperty("baseline_prediction") double baselinePrediction,
            @JsonProperty("scenario_prediction") double scenarioPrediction,
            @JsonProperty("absolute_difference") double absoluteDifference,
            @JsonProperty("percentage_difference") Double percentageDifference,
            @JsonProperty("model_version") String modelVersion,
            @JsonProperty("baseline_warnings") List<RangeWarning> baselineWarnings,
            @JsonProperty("scenario_warnings") List<RangeWarning> scenarioWarnings,
            String disclaimer,
            @JsonProperty("request_id") String requestId) {
    }

    public record HealthResponse(String status, String service,
                                 @JsonProperty("dataset_loaded") boolean datasetLoaded,
                                 @JsonProperty("row_count") int rowCount,
                                 @JsonProperty("ml_api_status") String mlApiStatus) {
    }

    public record ReadyResponse(String status, String service) {
    }

    public record ErrorDetail(String field, String message) {
    }

    public record ErrorBody(String code, String message, List<ErrorDetail> details,
                            @JsonProperty("request_id") String requestId) {
    }

    public record ErrorEnvelope(ErrorBody error) {
    }

    public record ExportMetadata(Instant generatedAt, Map<String, Number> filters) {
    }
}
