package com.example.housing.market.model;

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
        return new PropertyFeatures(squareFootage, bedrooms, bathrooms, yearBuilt, lotSize,
                distanceToCityCenter, schoolRating);
    }
}
