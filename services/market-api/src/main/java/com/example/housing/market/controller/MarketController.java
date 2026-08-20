package com.example.housing.market.controller;

import com.example.housing.market.client.MlApiClient;
import com.example.housing.market.data.DatasetRepository;
import com.example.housing.market.data.DatasetRepository.DatasetNotReadyException;
import com.example.housing.market.model.ApiModels.ErrorBody;
import com.example.housing.market.model.ApiModels.ErrorEnvelope;
import com.example.housing.market.model.ApiModels.HealthResponse;
import com.example.housing.market.model.ApiModels.MarketSummary;
import com.example.housing.market.model.ApiModels.PropertyPage;
import com.example.housing.market.model.ApiModels.ReadyResponse;
import com.example.housing.market.model.ApiModels.SegmentResponse;
import com.example.housing.market.model.ApiModels.WhatIfRequest;
import com.example.housing.market.model.ApiModels.WhatIfResponse;
import com.example.housing.market.model.MarketProperty;
import com.example.housing.market.service.ExportService;
import com.example.housing.market.service.MarketFilters;
import com.example.housing.market.service.MarketService;
import com.example.housing.market.web.RequestIdFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.BindParam;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.DateTimeException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;

/**
 * Exposes the market HTTP contract while delegating filtering, statistics, exports, and ML calls
 * to their owning layers. Keeping this class thin makes protocol binding independently testable.
 */
@RestController
@RequestMapping
public class MarketController {
    private static final String DISCLAIMER =
            "This comparison is a model association, not a causal estimate.";

    private final MarketService marketService;
    private final ExportService exportService;
    private final DatasetRepository repository;
    private final MlApiClient mlApiClient;
    private final Clock clock;

    public MarketController(MarketService marketService, ExportService exportService,
                            DatasetRepository repository, MlApiClient mlApiClient) {
        this.marketService = marketService;
        this.exportService = exportService;
        this.repository = repository;
        this.mlApiClient = mlApiClient;
        this.clock = Clock.systemUTC();
    }

    @GetMapping("/api/v1/market/summary")
    public MarketSummary summary(@ModelAttribute FilterParameters parameters,
                                 HttpServletRequest request) {
        return marketService.summary(parameters.filters(), RequestIdFilter.requestId(request));
    }

    @GetMapping("/api/v1/market/properties")
    public PropertyPage properties(@ModelAttribute FilterParameters parameters,
                                   @RequestParam(defaultValue = "0") int page,
                                   @RequestParam(defaultValue = "20") int size,
                                   @RequestParam(defaultValue = "id,asc") String sort,
                                   HttpServletRequest request) {
        return marketService.properties(parameters.filters(), page, size, sort,
                RequestIdFilter.requestId(request));
    }

    @GetMapping("/api/v1/market/segments")
    public SegmentResponse segments(@ModelAttribute FilterParameters parameters,
                                    @RequestParam("group_by") String groupBy,
                                    HttpServletRequest request) {
        return marketService.segments(parameters.filters(), groupBy,
                RequestIdFilter.requestId(request));
    }

    @PostMapping("/api/v1/market/what-if")
    public WhatIfResponse whatIf(@Valid @RequestBody WhatIfRequest whatIf,
                                 HttpServletRequest request) {
        String requestId = RequestIdFilter.requestId(request);
        // The client validates these batch indexes, so position 0 is always baseline and 1 scenario.
        MlApiClient.PredictionResponse result = mlApiClient.predict(
                List.of(whatIf.baseline(), whatIf.scenario()), requestId);
        double baseline = result.predictions().get(0).predictedPrice();
        double scenario = result.predictions().get(1).predictedPrice();
        double difference = scenario - baseline;
        // A boxed Double allows JSON null when division by zero makes the percentage undefined.
        Double percentage = baseline == 0 ? null : BigDecimal.valueOf(difference / baseline * 100)
                .setScale(2, RoundingMode.HALF_UP).doubleValue();
        return new WhatIfResponse(baseline, scenario, difference, percentage, result.modelVersion(),
                result.predictions().get(0).warnings(), result.predictions().get(1).warnings(),
                DISCLAIMER, requestId);
    }

    @GetMapping("/api/v1/market/export")
    public ResponseEntity<byte[]> export(@ModelAttribute FilterParameters parameters,
                                         @RequestParam String format,
                                         @RequestParam(name = "time_zone", defaultValue = "UTC")
                                         String timeZone) {
        // Validate before reading rows so both CSV and PDF apply exactly the same filter semantics.
        MarketFilters filters = parameters.filters().validated();
        List<MarketProperty> rows = marketService.filtered(filters);
        Instant generatedAt = clock.instant();
        // The caller's IANA zone controls both the visible PDF timestamp and dated filename.
        ZoneId zoneId = parseTimeZone(timeZone);
        String normalized = format.toLowerCase();
        byte[] content;
        MediaType mediaType;
        if (normalized.equals("csv")) {
            content = exportService.csv(rows);
            mediaType = new MediaType("text", "csv", java.nio.charset.StandardCharsets.UTF_8);
        } else if (normalized.equals("pdf")) {
            content = exportService.pdf(rows, filters.applied(), generatedAt, zoneId);
            mediaType = MediaType.APPLICATION_PDF;
        } else {
            throw new IllegalArgumentException("format must be csv or pdf");
        }
        String filename = "market-export-" + LocalDate.ofInstant(generatedAt, zoneId)
                .toString().replace("-", "") + "." + normalized;
        // Content-Disposition uses Spring's builder to quote and escape attachment names safely.
        return ResponseEntity.ok()
                .contentType(mediaType)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment().filename(filename).build().toString())
                .body(content);
    }

    private static ZoneId parseTimeZone(String timeZone) {
        try {
            return ZoneId.of(timeZone);
        } catch (DateTimeException exception) {
            throw new IllegalArgumentException("time_zone must be a valid IANA time zone");
        }
    }

    @GetMapping("/health")
    public ResponseEntity<?> health(HttpServletRequest request) {
        boolean mlUp = mlApiClient.health();
        if (!repository.loaded()) {
            return ResponseEntity.status(503).body(new ErrorEnvelope(new ErrorBody(
                    "DATASET_NOT_READY", "Market dataset is not ready.", List.of(),
                    RequestIdFilter.requestId(request))));
        }
        // Liveness remains 200 in a degraded state because this process can still serve market data.
        return ResponseEntity.ok(new HealthResponse(mlUp ? "healthy" : "degraded", "market-api",
                true, repository.rowCount(), mlUp ? "up" : "down"));
    }

    @GetMapping("/ready")
    public ResponseEntity<?> ready(HttpServletRequest request) {
        if (!repository.loaded()) {
            throw new DatasetNotReadyException("Market dataset is not ready");
        }
        if (!mlApiClient.ready()) {
            // Readiness is stricter than health: traffic must wait until the prediction dependency is ready.
            return ResponseEntity.status(503).body(new ErrorEnvelope(new ErrorBody(
                    "UPSTREAM_UNAVAILABLE", "ML API is not ready.", List.of(),
                    RequestIdFilter.requestId(request))));
        }
        return ResponseEntity.ok(new ReadyResponse("healthy", "market-api"));
    }

    /**
     * Spring binds query parameters to this immutable record. {@link BindParam} preserves the
     * public snake_case API while the Java components retain idiomatic camelCase names.
     */
    public record FilterParameters(
            @BindParam("min_price") Double minPrice,
            @BindParam("max_price") Double maxPrice,
            @BindParam("bedrooms") Integer bedrooms,
            @BindParam("min_square_footage") Double minSquareFootage,
            @BindParam("max_square_footage") Double maxSquareFootage,
            @BindParam("min_bathrooms") Double minBathrooms,
            @BindParam("min_year_built") Integer minYearBuilt,
            @BindParam("max_year_built") Integer maxYearBuilt,
            @BindParam("min_school_rating") Double minSchoolRating,
            @BindParam("max_distance_to_city_center")
            Double maxDistanceToCityCenter) {
        MarketFilters filters() {
            // Conversion to the service-layer value object prevents HTTP binding concerns from leaking inward.
            return new MarketFilters(minPrice, maxPrice, bedrooms, minSquareFootage,
                    maxSquareFootage, minBathrooms, minYearBuilt, maxYearBuilt,
                    minSchoolRating, maxDistanceToCityCenter);
        }
    }
}
