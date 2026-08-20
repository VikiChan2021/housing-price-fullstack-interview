package com.example.housing.market.controller;

import com.example.housing.market.client.MlApiClient;
import com.example.housing.market.data.DatasetRepository;
import com.example.housing.market.model.ApiModels.CacheInfo;
import com.example.housing.market.model.ApiModels.MarketSummary;
import com.example.housing.market.service.ExportService;
import com.example.housing.market.service.MarketFilters;
import com.example.housing.market.service.MarketService;
import com.example.housing.market.web.ApiExceptionHandler;
import com.example.housing.market.web.RequestIdFilter;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

import java.time.ZoneId;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Uses a Spring MVC slice to test query binding, filters, status codes, headers, and JSON without
 * starting the full application or making real downstream calls.
 */
@WebMvcTest(MarketController.class)
@Import({ApiExceptionHandler.class, RequestIdFilter.class})
class MarketControllerTest {
    @Autowired
    private MockMvc mockMvc;

    // Spring inserts this mock into the MVC application context used by the controller.
    @MockitoBean
    private MarketService marketService;

    @MockitoBean
    private ExportService exportService;

    @MockitoBean
    private DatasetRepository repository;

    @MockitoBean
    private MlApiClient mlApiClient;

    @Test
    void bindsSnakeCaseFiltersAndReturnsRequestId() throws Exception {
        // thenAnswer copies the runtime request ID argument into the mocked response.
        when(marketService.summary(any(), anyString())).thenAnswer(invocation ->
                new MarketSummary(1, 300000d, 300000d, 300000d, 300000d, 1800d,
                        Map.of("min_price", 250000d), new CacheInfo(false, 300),
                        invocation.getArgument(1)));

        mockMvc.perform(get("/api/v1/market/summary")
                        .queryParam("min_price", "250000")
                        .header("X-Request-ID", "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Request-ID", "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"))
                .andExpect(jsonPath("$.count").value(1))
                .andExpect(jsonPath("$.request_id").value("5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"));

        ArgumentCaptor<MarketFilters> filters = ArgumentCaptor.forClass(MarketFilters.class);
        // Capturing the argument verifies protocol-to-domain conversion, not only response rendering.
        verify(marketService).summary(filters.capture(), anyString());
        assertThat(filters.getValue().minPrice()).isEqualTo(250000d);
    }

    @Test
    void healthShowsDatasetAndMlState() throws Exception {
        when(repository.loaded()).thenReturn(true);
        when(repository.rowCount()).thenReturn(50);
        when(mlApiClient.health()).thenReturn(true);

        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.dataset_loaded").value(true))
                .andExpect(jsonPath("$.row_count").value(50))
                .andExpect(jsonPath("$.ml_api_status").value("up"));
    }

    @Test
    void readinessIsStableWhenMlIsDown() throws Exception {
        when(repository.loaded()).thenReturn(true);
        when(mlApiClient.ready()).thenReturn(false);

        mockMvc.perform(get("/ready"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error.code").value("UPSTREAM_UNAVAILABLE"));
    }

    @Test
    void exportUsesRequestedBrowserTimeZone() throws Exception {
        when(marketService.filtered(any())).thenReturn(List.of());
        when(exportService.pdf(any(), any(), any(), any())).thenReturn(new byte[]{1, 2, 3});

        mockMvc.perform(get("/api/v1/market/export")
                        .queryParam("format", "pdf")
                        .queryParam("time_zone", "Asia/Hong_Kong"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", "application/pdf"));

        verify(exportService).pdf(any(), any(), any(), eq(ZoneId.of("Asia/Hong_Kong")));
    }
}
