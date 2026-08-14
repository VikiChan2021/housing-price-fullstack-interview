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
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;

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
        MlApiClient.PredictionResponse result = mlApiClient.predict(
                List.of(whatIf.baseline(), whatIf.scenario()), requestId);
        double baseline = result.predictions().get(0).predictedPrice();
        double scenario = result.predictions().get(1).predictedPrice();
        double difference = scenario - baseline;
        Double percentage = baseline == 0 ? null : BigDecimal.valueOf(difference / baseline * 100)
                .setScale(2, RoundingMode.HALF_UP).doubleValue();
        return new WhatIfResponse(baseline, scenario, difference, percentage, result.modelVersion(),
                result.predictions().get(0).warnings(), result.predictions().get(1).warnings(),
                DISCLAIMER, requestId);
    }

    @GetMapping("/api/v1/market/export")
    public ResponseEntity<byte[]> export(@ModelAttribute FilterParameters parameters,
                                         @RequestParam String format) {
        MarketFilters filters = parameters.filters().validated();
        List<MarketProperty> rows = marketService.filtered(filters);
        Instant generatedAt = clock.instant();
        String normalized = format.toLowerCase();
        byte[] content;
        MediaType mediaType;
        if (normalized.equals("csv")) {
            content = exportService.csv(rows);
            mediaType = new MediaType("text", "csv", java.nio.charset.StandardCharsets.UTF_8);
        } else if (normalized.equals("pdf")) {
            content = exportService.pdf(rows, filters.applied(), generatedAt);
            mediaType = MediaType.APPLICATION_PDF;
        } else {
            throw new IllegalArgumentException("format must be csv or pdf");
        }
        String filename = "market-export-" + LocalDate.ofInstant(generatedAt, ZoneOffset.UTC)
                .toString().replace("-", "") + "." + normalized;
        return ResponseEntity.ok()
                .contentType(mediaType)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment().filename(filename).build().toString())
                .body(content);
    }

    @GetMapping("/health")
    public ResponseEntity<?> health(HttpServletRequest request) {
        boolean mlUp = mlApiClient.health();
        if (!repository.loaded()) {
            return ResponseEntity.status(503).body(new ErrorEnvelope(new ErrorBody(
                    "DATASET_NOT_READY", "Market dataset is not ready.", List.of(),
                    RequestIdFilter.requestId(request))));
        }
        return ResponseEntity.ok(new HealthResponse(mlUp ? "healthy" : "degraded", "market-api",
                true, repository.rowCount(), mlUp ? "up" : "down"));
    }

    @GetMapping("/ready")
    public ResponseEntity<?> ready(HttpServletRequest request) {
        if (!repository.loaded()) {
            throw new DatasetNotReadyException("Market dataset is not ready");
        }
        if (!mlApiClient.ready()) {
            return ResponseEntity.status(503).body(new ErrorEnvelope(new ErrorBody(
                    "UPSTREAM_UNAVAILABLE", "ML API is not ready.", List.of(),
                    RequestIdFilter.requestId(request))));
        }
        return ResponseEntity.ok(new ReadyResponse("healthy", "market-api"));
    }

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
            return new MarketFilters(minPrice, maxPrice, bedrooms, minSquareFootage,
                    maxSquareFootage, minBathrooms, minYearBuilt, maxYearBuilt,
                    minSchoolRating, maxDistanceToCityCenter);
        }
    }
}
