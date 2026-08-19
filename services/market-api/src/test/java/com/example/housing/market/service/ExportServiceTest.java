package com.example.housing.market.service;

import com.example.housing.market.data.DatasetRepository;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.ZoneId;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class ExportServiceTest {
    private final ExportService service = new ExportService();

    @Test
    void csvHasBomHeaderAndAllFilteredRows() {
        DatasetRepository repository = loadedRepository();
        byte[] csv = service.csv(repository.rows());
        String text = new String(csv, StandardCharsets.UTF_8);

        assertThat(text).startsWith("\uFEFFid,square_footage,bedrooms");
        assertThat(text.lines()).hasSize(51);
        assertThat(text).contains("1,1250.0,2,1.0,1985");
    }

    @Test
    void pdfIsReadableAndContainsReportContext() throws Exception {
        DatasetRepository repository = loadedRepository();
        byte[] pdf = service.pdf(repository.rows(), Map.of(
                        "min_price", 200000,
                        "max_price", 19_999_999d),
                Instant.parse("2026-08-14T00:00:00Z"), ZoneId.of("Asia/Hong_Kong"));

        assertThat(pdf).startsWith("%PDF".getBytes(StandardCharsets.US_ASCII));
        try (PDDocument document = Loader.loadPDF(pdf)) {
            String text = new PDFTextStripper().getText(document);
            assertThat(document.getNumberOfPages()).isGreaterThanOrEqualTo(2);
            assertThat(text).contains(
                    "Housing Market Export",
                    "Generated: Aug 14, 2026, 8:00 AM HKT",
                    "Time zone: Asia/Hong_Kong",
                    "Minimum price: $200,000",
                    "Maximum price: $19,999,999",
                    "MATCHING HOMES",
                    "AVERAGE PRICE",
                    "LIVING AREA",
                    "DISTANCE",
                    "Page 1");
            assertThat(text).doesNotContain("1.9999999E7");
        }
    }

    @Test
    void emptyPdfIsStillValidAndExplicit() throws Exception {
        byte[] pdf = service.pdf(java.util.List.of(), Map.of(), Instant.EPOCH,
                ZoneId.of("UTC"));
        try (PDDocument document = Loader.loadPDF(pdf)) {
            assertThat(new PDFTextStripper().getText(document)).contains("No matching data");
        }
    }

    private static DatasetRepository loadedRepository() {
        DatasetRepository repository = new DatasetRepository("../../data/raw/House Price Dataset.csv");
        repository.load();
        return repository;
    }
}
