package com.example.housing.market.model;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public record PropertyFeatures(
        @NotNull @DecimalMin(value = "0", inclusive = false) @DecimalMax("100000") Double squareFootage,
        @NotNull @Min(0) @Max(100) Integer bedrooms,
        @NotNull @DecimalMin("0") @DecimalMax("100") Double bathrooms,
        @NotNull @Min(1600) @Max(2100) Integer yearBuilt,
        @NotNull @DecimalMin(value = "0", inclusive = false) @DecimalMax("100000000") Double lotSize,
        @NotNull @DecimalMin("0") @DecimalMax("10000") Double distanceToCityCenter,
        @NotNull @DecimalMin("0") @DecimalMax("10") Double schoolRating) {
}
