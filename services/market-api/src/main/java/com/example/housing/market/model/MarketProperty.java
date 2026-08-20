package com.example.housing.market.model;

/**
 * Immutable representation of one source CSV row. Java records generate accessors, value-based
 * equality, {@code hashCode}, and {@code toString} while keeping the data shape explicit.
 */
public record MarketProperty(
        int id,
        double squareFootage,
        int bedrooms,
        double bathrooms,
        int yearBuilt,
        double lotSize,
        double distanceToCityCenter,
        double schoolRating,
        double price) {

    public PropertyFeatures features() {
        // The source ID identifies a row but is intentionally excluded from model inference features.
        return new PropertyFeatures(squareFootage, bedrooms, bathrooms, yearBuilt, lotSize,
                distanceToCityCenter, schoolRating);
    }
}
