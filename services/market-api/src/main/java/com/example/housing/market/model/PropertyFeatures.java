package com.example.housing.market.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public record PropertyFeatures(
        @JsonProperty("square_footage")
        @NotNull @DecimalMin(value = "0", inclusive = false) @DecimalMax("100000") Double squareFootage,
        @JsonProperty("bedrooms")
        @NotNull @Min(0) @Max(100) Integer bedrooms,
        @JsonProperty("bathrooms")
        @NotNull @DecimalMin("0") @DecimalMax("100") Double bathrooms,
        @JsonProperty("year_built")
        @NotNull @Min(1600) @Max(2100) Integer yearBuilt,
        @JsonProperty("lot_size")
        @NotNull @DecimalMin(value = "0", inclusive = false) @DecimalMax("100000000") Double lotSize,
        @JsonProperty("distance_to_city_center")
        @NotNull @DecimalMin("0") @DecimalMax("10000") Double distanceToCityCenter,
        @JsonProperty("school_rating")
        @NotNull @DecimalMin("0") @DecimalMax("10") Double schoolRating) {
}
