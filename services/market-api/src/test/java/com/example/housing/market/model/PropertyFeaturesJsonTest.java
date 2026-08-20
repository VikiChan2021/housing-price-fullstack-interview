package com.example.housing.market.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/** Ensures Java naming conventions cannot accidentally drift from the ML API wire contract. */
class PropertyFeaturesJsonTest {
    @Test
    void serializesTheMlContractFieldNames() throws Exception {
        PropertyFeatures features = new PropertyFeatures(
                1550.0, 3, 2.0, 1997, 6800.0, 4.1, 7.6);

        String json = new ObjectMapper().writeValueAsString(features);

        // Positive and negative assertions catch both missing snake_case and leaked camelCase names.
        assertThat(json).contains("\"square_footage\":1550.0")
                .contains("\"year_built\":1997")
                .contains("\"distance_to_city_center\":4.1")
                .doesNotContain("squareFootage", "yearBuilt", "distanceToCityCenter");
    }
}
