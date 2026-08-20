package com.example.housing.market.data;

import com.example.housing.market.model.MarketProperty;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Loads and validates the immutable interview dataset into an in-memory snapshot.
 *
 * <p>The service deliberately keeps startup alive when loading fails. Health and readiness
 * endpoints can then expose a diagnosable {@code DATASET_NOT_READY} state instead of making the
 * entire process disappear.</p>
 */
@Component
public class DatasetRepository {
    private static final String HEADER = "id,square_footage,bedrooms,bathrooms,year_built,lot_size,"
            + "distance_to_city_center,school_rating,price";

    private final Path path;
    // Volatile publishes each complete immutable snapshot safely to request-handling threads.
    private volatile List<MarketProperty> rows = List.of();
    private volatile String loadError;

    public DatasetRepository(@Value("${market.data-path}") String path) {
        this.path = Path.of(path);
    }

    @PostConstruct
    public void load() {
        try {
            List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
            // Excel-style UTF-8 CSV files may prefix the first header with a byte-order mark.
            if (lines.isEmpty() || !lines.getFirst().replace("\uFEFF", "").equals(HEADER)) {
                throw new IllegalStateException("Dataset columns do not match the contract");
            }
            List<MarketProperty> loaded = new ArrayList<>();
            Set<Integer> identifiers = new HashSet<>();
            for (int index = 1; index < lines.size(); index++) {
                String[] values = lines.get(index).split(",", -1);
                if (values.length != 9) {
                    throw new IllegalStateException("Invalid dataset row " + index);
                }
                MarketProperty property = parse(values, index);
                // IDs identify source records; uniqueness is checked even though IDs are not ML features.
                if (!identifiers.add(property.id())) {
                    throw new IllegalStateException("Duplicate dataset id " + property.id());
                }
                loaded.add(property);
            }
            if (loaded.size() != 50) {
                throw new IllegalStateException("Expected 50 dataset rows, found " + loaded.size());
            }
            rows = List.copyOf(loaded);
            loadError = null;
        } catch (IOException | RuntimeException exception) {
            // Clear any previous snapshot so callers can never consume stale data after a failed reload.
            rows = List.of();
            loadError = exception.getMessage();
        }
    }

    private static MarketProperty parse(String[] values, int row) {
        try {
            // The source contract is numeric-only, so a simple split is sufficient and predictable.
            MarketProperty property = new MarketProperty(
                    Integer.parseInt(values[0]), Double.parseDouble(values[1]),
                    Integer.parseInt(values[2]), Double.parseDouble(values[3]),
                    Integer.parseInt(values[4]), Double.parseDouble(values[5]),
                    Double.parseDouble(values[6]), Double.parseDouble(values[7]),
                    Double.parseDouble(values[8]));
            if (property.id() < 1 || property.price() <= 0
                    || !Double.isFinite(property.price()) || !Double.isFinite(property.squareFootage())) {
                throw new IllegalArgumentException("Non-finite or out-of-range value");
            }
            return property;
        } catch (NumberFormatException exception) {
            throw new IllegalStateException("Invalid number at dataset row " + row, exception);
        }
    }

    public List<MarketProperty> rows() {
        if (!loaded()) {
            throw new DatasetNotReadyException(loadError == null ? "Dataset is not ready" : loadError);
        }
        // The published list is immutable, so callers can filter it without defensive copying.
        return rows;
    }

    public boolean loaded() {
        return loadError == null && !rows.isEmpty();
    }

    public int rowCount() {
        return rows.size();
    }

    public static class DatasetNotReadyException extends RuntimeException {
        public DatasetNotReadyException(String message) {
            super(message);
        }
    }
}
