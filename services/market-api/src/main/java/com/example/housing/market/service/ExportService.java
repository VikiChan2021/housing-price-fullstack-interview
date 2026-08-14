package com.example.housing.market.service;

import com.example.housing.market.model.MarketProperty;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class ExportService {
    private static final String CSV_HEADER = "id,square_footage,bedrooms,bathrooms,year_built,"
            + "lot_size,distance_to_city_center,school_rating,price\r\n";

    public byte[] csv(List<MarketProperty> rows) {
        StringBuilder csv = new StringBuilder("\uFEFF").append(CSV_HEADER);
        for (MarketProperty row : rows) {
            csv.append(row.id()).append(',').append(row.squareFootage()).append(',')
                    .append(row.bedrooms()).append(',').append(row.bathrooms()).append(',')
                    .append(row.yearBuilt()).append(',').append(row.lotSize()).append(',')
                    .append(row.distanceToCityCenter()).append(',').append(row.schoolRating()).append(',')
                    .append(row.price()).append("\r\n");
        }
        return csv.toString().getBytes(StandardCharsets.UTF_8);
    }

    public byte[] pdf(List<MarketProperty> rows, Map<String, Number> filters, Instant generatedAt) {
        try (PDDocument document = new PDDocument(); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            List<String> lines = new ArrayList<>();
            lines.add("Housing Market Export");
            lines.add("Generated UTC: " + generatedAt);
            lines.add("Filters: " + (filters.isEmpty() ? "none" : filters));
            lines.add("Matching properties: " + rows.size());
            lines.add("");
            if (rows.isEmpty()) {
                lines.add("No matching data");
            } else {
                lines.add("ID | Sq Ft | Beds | Baths | Year | Price");
                for (MarketProperty row : rows) {
                    lines.add(String.format(Locale.ROOT, "%d | %.0f | %d | %.1f | %d | $%.2f",
                            row.id(), row.squareFootage(), row.bedrooms(), row.bathrooms(),
                            row.yearBuilt(), row.price()));
                }
            }
            writePages(document, lines);
            document.save(output);
            return output.toByteArray();
        } catch (IOException exception) {
            throw new ExportFailedException("Unable to generate PDF", exception);
        }
    }

    private static void writePages(PDDocument document, List<String> lines) throws IOException {
        PDType1Font font = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
        int index = 0;
        while (index < lines.size()) {
            PDPage page = new PDPage(PDRectangle.LETTER);
            document.addPage(page);
            try (PDPageContentStream content = new PDPageContentStream(document, page)) {
                content.beginText();
                content.setFont(font, 10);
                content.newLineAtOffset(45, 745);
                int linesOnPage = 0;
                while (index < lines.size() && linesOnPage < 48) {
                    content.showText(lines.get(index).replaceAll("[^\\x20-\\x7E]", "?"));
                    content.newLineAtOffset(0, -14);
                    index++;
                    linesOnPage++;
                }
                content.endText();
            }
        }
    }

    public static class ExportFailedException extends RuntimeException {
        public ExportFailedException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
