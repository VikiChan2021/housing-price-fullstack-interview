package com.example.housing.market.service;

import com.example.housing.market.model.MarketProperty;

import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;

public record MarketFilters(
        Double minPrice, Double maxPrice, Integer bedrooms,
        Double minSquareFootage, Double maxSquareFootage, Double minBathrooms,
        Integer minYearBuilt, Integer maxYearBuilt, Double minSchoolRating,
        Double maxDistanceToCityCenter) {

    public MarketFilters validated() {
        checkFinite(minPrice, "min_price");
        checkFinite(maxPrice, "max_price");
        checkFinite(minSquareFootage, "min_square_footage");
        checkFinite(maxSquareFootage, "max_square_footage");
        checkFinite(minBathrooms, "min_bathrooms");
        checkFinite(minSchoolRating, "min_school_rating");
        checkFinite(maxDistanceToCityCenter, "max_distance_to_city_center");
        if (minPrice != null && minPrice < 0 || maxPrice != null && maxPrice < 0) {
            throw new IllegalArgumentException("price filters must be >= 0");
        }
        if (minPrice != null && maxPrice != null && minPrice > maxPrice) {
            throw new IllegalArgumentException("min_price must be <= max_price");
        }
        if (minSquareFootage != null && maxSquareFootage != null
                && minSquareFootage > maxSquareFootage) {
            throw new IllegalArgumentException("min_square_footage must be <= max_square_footage");
        }
        if (minYearBuilt != null && maxYearBuilt != null && minYearBuilt > maxYearBuilt) {
            throw new IllegalArgumentException("min_year_built must be <= max_year_built");
        }
        if (bedrooms != null && (bedrooms < 0 || bedrooms > 100)) {
            throw new IllegalArgumentException("bedrooms must be between 0 and 100");
        }
        positiveBound(minSquareFootage, "min_square_footage", 100_000, true);
        positiveBound(maxSquareFootage, "max_square_footage", 100_000, true);
        positiveBound(minBathrooms, "min_bathrooms", 100, false);
        positiveBound(minSchoolRating, "min_school_rating", 10, false);
        positiveBound(maxDistanceToCityCenter, "max_distance_to_city_center", 10_000, false);
        if (minYearBuilt != null && (minYearBuilt < 1600 || minYearBuilt > 2100)
                || maxYearBuilt != null && (maxYearBuilt < 1600 || maxYearBuilt > 2100)) {
            throw new IllegalArgumentException("year filters must be between 1600 and 2100");
        }
        return this;
    }

    private static void positiveBound(Double value, String field, double max, boolean exclusiveZero) {
        if (value != null && (value > max || value < 0 || exclusiveZero && value == 0)) {
            throw new IllegalArgumentException(field + " is outside the allowed range");
        }
    }

    private static void checkFinite(Double value, String field) {
        if (value != null && !Double.isFinite(value)) {
            throw new IllegalArgumentException(field + " must be finite");
        }
    }

    public boolean matches(MarketProperty row) {
        return (minPrice == null || row.price() >= minPrice)
                && (maxPrice == null || row.price() <= maxPrice)
                && (bedrooms == null || row.bedrooms() == bedrooms)
                && (minSquareFootage == null || row.squareFootage() >= minSquareFootage)
                && (maxSquareFootage == null || row.squareFootage() <= maxSquareFootage)
                && (minBathrooms == null || row.bathrooms() >= minBathrooms)
                && (minYearBuilt == null || row.yearBuilt() >= minYearBuilt)
                && (maxYearBuilt == null || row.yearBuilt() <= maxYearBuilt)
                && (minSchoolRating == null || row.schoolRating() >= minSchoolRating)
                && (maxDistanceToCityCenter == null
                || row.distanceToCityCenter() <= maxDistanceToCityCenter);
    }

    public Map<String, Number> applied() {
        Map<String, Number> values = new TreeMap<>();
        put(values, "min_price", minPrice);
        put(values, "max_price", maxPrice);
        put(values, "bedrooms", bedrooms);
        put(values, "min_square_footage", minSquareFootage);
        put(values, "max_square_footage", maxSquareFootage);
        put(values, "min_bathrooms", minBathrooms);
        put(values, "min_year_built", minYearBuilt);
        put(values, "max_year_built", maxYearBuilt);
        put(values, "min_school_rating", minSchoolRating);
        put(values, "max_distance_to_city_center", maxDistanceToCityCenter);
        return Map.copyOf(values);
    }

    private static void put(Map<String, Number> values, String name, Number value) {
        if (value != null) {
            values.put(name, value);
        }
    }

    public String normalizedKey() {
        return applied().entrySet().stream()
                .map(entry -> entry.getKey() + "=" + normalize(entry.getValue()))
                .collect(Collectors.joining("&"));
    }

    private static String normalize(Number value) {
        double number = value.doubleValue();
        return number == Math.rint(number) ? Long.toString((long) number) : Double.toString(number);
    }
}
