package com.example.housing.market.service;

import com.example.housing.market.data.DatasetRepository;
import com.example.housing.market.model.ApiModels.MarketSummary;
import com.example.housing.market.model.ApiModels.PropertyPage;
import com.example.housing.market.model.ApiModels.SegmentResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MarketServiceTest {
    private DatasetRepository repository;
    private MarketService service;

    @BeforeEach
    void setUp() {
        repository = new DatasetRepository("../../data/raw/House Price Dataset.csv");
        repository.load();
        service = new MarketService(repository, 300, 256);
    }

    @Test
    void loadsExactDatasetAndCalculatesSourceBackedSummary() {
        MarketSummary first = service.summary(emptyFilters(), "request-1");
        MarketSummary second = service.summary(emptyFilters(), "request-2");

        assertThat(repository.loaded()).isTrue();
        assertThat(repository.rowCount()).isEqualTo(50);
        assertThat(first.count()).isEqualTo(50);
        assertThat(first.averagePrice()).isEqualTo(264600.0);
        assertThat(first.medianPrice()).isEqualTo(245000.0);
        assertThat(first.minPrice()).isEqualTo(160000.0);
        assertThat(first.maxPrice()).isEqualTo(410000.0);
        assertThat(first.averageSquareFootage()).isEqualTo(1690.2);
        assertThat(first.cache().hit()).isFalse();
        assertThat(second.cache().hit()).isTrue();
        assertThat(service.cacheHitCount()).isEqualTo(1);
    }

    @Test
    void normalizesCacheKeysAndSeparatesDifferentFilters() {
        MarketFilters integerStyle = new MarketFilters(200000.0, null, 3, null, null,
                null, null, null, null, null);
        MarketFilters sameValues = new MarketFilters(200000d, null, 3, null, null,
                null, null, null, null, null);
        MarketFilters different = new MarketFilters(300000d, null, 3, null, null,
                null, null, null, null, null);

        assertThat(integerStyle.normalizedKey()).isEqualTo(sameValues.normalizedKey());
        assertThat(integerStyle.normalizedKey()).isNotEqualTo(different.normalizedKey());
        assertThat(service.summary(integerStyle, "one").cache().hit()).isFalse();
        assertThat(service.summary(sameValues, "two").cache().hit()).isTrue();
        assertThat(service.summary(different, "three").cache().hit()).isFalse();
    }

    @Test
    void filtersSortsPaginatesAndSegments() {
        MarketFilters filters = new MarketFilters(250000d, null, null, null, null,
                null, null, null, null, null);
        PropertyPage page = service.properties(filters, 0, 5, "price,desc", "request");
        SegmentResponse segments = service.segments(filters, "bedrooms", "request");

        assertThat(page.items()).hasSize(5).isSortedAccordingTo(
                (left, right) -> Double.compare(right.price(), left.price()));
        assertThat(page.items()).allMatch(row -> row.price() >= 250000);
        assertThat(page.totalItems()).isGreaterThan(5);
        assertThat(segments.segments()).isNotEmpty();
        assertThat(segments.segments()).extracting(segment -> Integer.parseInt(segment.key()))
                .isSorted();
    }

    @Test
    void rejectsInvertedFiltersAndUnapprovedSorts() {
        MarketFilters inverted = new MarketFilters(300000d, 200000d, null, null, null,
                null, null, null, null, null);

        assertThatThrownBy(inverted::validated).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.properties(emptyFilters(), 0, 20, "unknown,asc", "id"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.segments(emptyFilters(), "unsafe", "id"))
                .isInstanceOf(IllegalArgumentException.class);
    }

    private static MarketFilters emptyFilters() {
        return new MarketFilters(null, null, null, null, null,
                null, null, null, null, null);
    }
}
