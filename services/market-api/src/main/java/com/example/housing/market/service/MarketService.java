package com.example.housing.market.service;

import com.example.housing.market.data.DatasetRepository;
import com.example.housing.market.model.ApiModels.CacheInfo;
import com.example.housing.market.model.ApiModels.MarketSummary;
import com.example.housing.market.model.ApiModels.PropertyPage;
import com.example.housing.market.model.ApiModels.Segment;
import com.example.housing.market.model.ApiModels.SegmentResponse;
import com.example.housing.market.model.MarketProperty;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class MarketService {
    private final DatasetRepository repository;
    private final Cache<String, SummaryValues> summaryCache;
    private final long ttlSeconds;

    public MarketService(DatasetRepository repository,
                         @Value("${market.cache-ttl-seconds}") long ttlSeconds,
                         @Value("${market.cache-max-entries}") long maxEntries) {
        this.repository = repository;
        this.ttlSeconds = ttlSeconds;
        this.summaryCache = Caffeine.newBuilder()
                .expireAfterWrite(Duration.ofSeconds(ttlSeconds))
                .maximumSize(maxEntries)
                .recordStats()
                .build();
    }

    public MarketSummary summary(MarketFilters rawFilters, String requestId) {
        MarketFilters filters = rawFilters.validated();
        String key = filters.normalizedKey();
        SummaryValues values = summaryCache.getIfPresent(key);
        boolean hit = values != null;
        if (values == null) {
            values = calculateSummary(filtered(filters));
            summaryCache.put(key, values);
        }
        return new MarketSummary(values.count(), values.averagePrice(), values.medianPrice(),
                values.minPrice(), values.maxPrice(), values.averageSquareFootage(),
                filters.applied(), new CacheInfo(hit, ttlSeconds), requestId);
    }

    public PropertyPage properties(MarketFilters rawFilters, int page, int size,
                                   String sort, String requestId) {
        MarketFilters filters = rawFilters.validated();
        if (page < 0 || size < 1 || size > 100) {
            throw new IllegalArgumentException("page must be >= 0 and size must be between 1 and 100");
        }
        Comparator<MarketProperty> comparator = comparator(sort);
        List<MarketProperty> rows = filtered(filters).stream().sorted(comparator).toList();
        int from = Math.min(page * size, rows.size());
        int to = Math.min(from + size, rows.size());
        int totalPages = rows.isEmpty() ? 0 : (rows.size() + size - 1) / size;
        return new PropertyPage(rows.subList(from, to), page, size, rows.size(), totalPages,
                normalizeSort(sort), filters.applied(), requestId);
    }

    public SegmentResponse segments(MarketFilters rawFilters, String groupBy, String requestId) {
        MarketFilters filters = rawFilters.validated();
        Function<MarketProperty, SegmentKey> classifier = switch (groupBy) {
            case "bedrooms" -> row -> new SegmentKey(row.bedrooms(), Integer.toString(row.bedrooms()),
                    row.bedrooms() + " bedrooms");
            case "year_band" -> row -> {
                int start = (row.yearBuilt() / 10) * 10;
                return new SegmentKey(start, Integer.toString(start), start + "-" + (start + 9));
            };
            case "price_band" -> row -> {
                int start = ((int) row.price() / 50_000) * 50_000;
                return new SegmentKey(start, Integer.toString(start),
                        "$" + start + "-$" + (start + 49_999));
            };
            default -> throw new IllegalArgumentException(
                    "group_by must be bedrooms, year_band, or price_band");
        };
        Map<SegmentKey, List<MarketProperty>> grouped = filtered(filters).stream()
                .collect(Collectors.groupingBy(classifier, LinkedHashMap::new, Collectors.toList()));
        List<Segment> segments = grouped.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> toSegment(entry.getKey(), entry.getValue()))
                .toList();
        return new SegmentResponse(groupBy, segments, filters.applied(), requestId);
    }

    public List<MarketProperty> filtered(MarketFilters rawFilters) {
        MarketFilters filters = rawFilters.validated();
        return repository.rows().stream().filter(filters::matches).toList();
    }

    private static SummaryValues calculateSummary(List<MarketProperty> rows) {
        if (rows.isEmpty()) {
            return new SummaryValues(0, null, null, null, null, null);
        }
        List<Double> prices = rows.stream().map(MarketProperty::price).sorted().toList();
        return new SummaryValues(rows.size(), prices.stream().mapToDouble(Double::doubleValue).average().orElseThrow(),
                median(prices), prices.getFirst(), prices.getLast(),
                rows.stream().mapToDouble(MarketProperty::squareFootage).average().orElseThrow());
    }

    private static Segment toSegment(SegmentKey key, List<MarketProperty> rows) {
        List<Double> prices = rows.stream().map(MarketProperty::price).sorted().toList();
        return new Segment(key.key(), key.label(), rows.size(),
                prices.stream().mapToDouble(Double::doubleValue).average().orElseThrow(), median(prices));
    }

    static double median(List<Double> sorted) {
        int middle = sorted.size() / 2;
        return sorted.size() % 2 == 0
                ? (sorted.get(middle - 1) + sorted.get(middle)) / 2.0
                : sorted.get(middle);
    }

    private static Comparator<MarketProperty> comparator(String rawSort) {
        String[] parts = normalizeSort(rawSort).split(",");
        Comparator<MarketProperty> comparator = switch (parts[0]) {
            case "id" -> Comparator.comparingInt(MarketProperty::id);
            case "price" -> Comparator.comparingDouble(MarketProperty::price);
            case "square_footage" -> Comparator.comparingDouble(MarketProperty::squareFootage);
            case "bedrooms" -> Comparator.comparingInt(MarketProperty::bedrooms);
            case "bathrooms" -> Comparator.comparingDouble(MarketProperty::bathrooms);
            case "year_built" -> Comparator.comparingInt(MarketProperty::yearBuilt);
            case "lot_size" -> Comparator.comparingDouble(MarketProperty::lotSize);
            case "distance_to_city_center" -> Comparator.comparingDouble(MarketProperty::distanceToCityCenter);
            case "school_rating" -> Comparator.comparingDouble(MarketProperty::schoolRating);
            default -> throw new IllegalArgumentException("Unsupported sort field: " + parts[0]);
        };
        return parts[1].equals("desc") ? comparator.reversed() : comparator;
    }

    private static String normalizeSort(String rawSort) {
        String sort = rawSort == null || rawSort.isBlank() ? "id,asc" : rawSort.toLowerCase();
        String[] parts = sort.split(",", -1);
        if (parts.length != 2 || !(parts[1].equals("asc") || parts[1].equals("desc"))) {
            throw new IllegalArgumentException("sort must use <field>,<asc|desc>");
        }
        return sort;
    }

    public long cacheHitCount() {
        return summaryCache.stats().hitCount();
    }

    private record SummaryValues(long count, Double averagePrice, Double medianPrice,
                                 Double minPrice, Double maxPrice, Double averageSquareFootage) {
    }

    private record SegmentKey(int order, String key, String label) implements Comparable<SegmentKey> {
        @Override
        public int compareTo(SegmentKey other) {
            return Integer.compare(order, other.order);
        }
    }
}
