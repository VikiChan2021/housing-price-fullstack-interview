package com.example.housing.market.service;

import com.example.housing.market.model.MarketProperty;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDFont;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Renders filtered market rows as spreadsheet-friendly CSV or a paginated PDF report.
 * Export formatting stays outside the controller so binary generation can be tested directly.
 */
@Service
public class ExportService {
    private static final String CSV_HEADER = "id,square_footage,bedrooms,bathrooms,year_built,"
            + "lot_size,distance_to_city_center,school_rating,price\r\n";
    private static final PDRectangle PAGE_SIZE = new PDRectangle(
            PDRectangle.LETTER.getHeight(), PDRectangle.LETTER.getWidth());
    private static final float PAGE_MARGIN = 40;
    private static final float CONTENT_WIDTH = PAGE_SIZE.getWidth() - PAGE_MARGIN * 2;
    private static final float TABLE_ROW_HEIGHT = 20;
    private static final float TABLE_HEADER_HEIGHT = 24;
    private static final PDFont REGULAR = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
    private static final PDFont BOLD = new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD);
    private static final List<Column> TABLE_COLUMNS = List.of(
            new Column("ID", 45), new Column("LIVING AREA", 90),
            new Column("BEDS", 55), new Column("BATHS", 55),
            new Column("YEAR", 65), new Column("LOT", 90),
            new Column("SCHOOL", 70), new Column("DISTANCE", 90),
            new Column("PRICE", 152));
    private static final List<FilterDefinition> FILTER_DEFINITIONS = List.of(
            new FilterDefinition("min_price", "Minimum price", FilterType.CURRENCY),
            new FilterDefinition("max_price", "Maximum price", FilterType.CURRENCY),
            new FilterDefinition("bedrooms", "Bedrooms", FilterType.NUMBER),
            new FilterDefinition("min_square_footage", "Minimum living area", FilterType.AREA),
            new FilterDefinition("max_square_footage", "Maximum living area", FilterType.AREA),
            new FilterDefinition("min_bathrooms", "Minimum bathrooms", FilterType.NUMBER),
            new FilterDefinition("min_year_built", "Earliest year built", FilterType.NUMBER),
            new FilterDefinition("max_year_built", "Latest year built", FilterType.NUMBER),
            new FilterDefinition("min_school_rating", "Minimum school rating", FilterType.NUMBER),
            new FilterDefinition("max_distance_to_city_center", "Maximum city distance",
                    FilterType.DISTANCE));

    public byte[] csv(List<MarketProperty> rows) {
        // The UTF-8 BOM improves Excel compatibility; CRLF keeps the downloaded file portable.
        StringBuilder csv = new StringBuilder("\uFEFF").append(CSV_HEADER);
        // Every source field is numeric, so no value can contain a comma, quote, or line break.
        for (MarketProperty row : rows) {
            csv.append(row.id()).append(',').append(row.squareFootage()).append(',')
                    .append(row.bedrooms()).append(',').append(row.bathrooms()).append(',')
                    .append(row.yearBuilt()).append(',').append(row.lotSize()).append(',')
                    .append(row.distanceToCityCenter()).append(',').append(row.schoolRating()).append(',')
                    .append(row.price()).append("\r\n");
        }
        return csv.toString().getBytes(StandardCharsets.UTF_8);
    }

    public byte[] pdf(List<MarketProperty> rows, Map<String, Number> filters, Instant generatedAt,
                      ZoneId timeZone) {
        // Try-with-resources closes both the PDF document and byte buffer on success or failure.
        try (PDDocument document = new PDDocument();
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            int rowIndex = 0;
            int pageNumber = 1;
            // A do-while intentionally creates one explanatory page even when no rows match.
            do {
                PDPage page = new PDPage(PAGE_SIZE);
                document.addPage(page);
                try (PDPageContentStream content = new PDPageContentStream(document, page)) {
                    float tableTop = pageNumber == 1
                            ? drawReportHeader(content, rows, filters, generatedAt, timeZone)
                            : drawContinuationHeader(content);
                    // drawTable returns the first row not yet rendered, which drives pagination.
                    rowIndex = drawTable(content, rows, rowIndex, tableTop);
                    drawFooter(content, pageNumber);
                }
                pageNumber++;
            } while (rowIndex < rows.size());

            document.save(output);
            return output.toByteArray();
        } catch (IOException exception) {
            throw new ExportFailedException("Unable to generate PDF", exception);
        }
    }

    private static float drawReportHeader(PDPageContentStream content, List<MarketProperty> rows,
                                          Map<String, Number> filters, Instant generatedAt,
                                          ZoneId timeZone) throws IOException {
        // PDF coordinates start at the bottom-left corner, so smaller y values move down the page.
        setGreen(content);
        drawText(content, BOLD, 9, PAGE_MARGIN, 570, "HEARTH & METRIC  /  MARKET ANALYSIS");
        setInk(content);
        drawText(content, BOLD, 24, PAGE_MARGIN, 535, "Housing Market Export");

        String timestamp = DateTimeFormatter.ofPattern("MMM d, uuuu, h:mm a z", Locale.US)
                // Formatting an Instant with an explicit zone avoids dependence on the server default.
                .withZone(timeZone).format(generatedAt);
        setMuted(content);
        drawText(content, REGULAR, 9, PAGE_MARGIN, 512,
                "Generated: " + timestamp + "  |  Time zone: " + timeZone.getId());
        setLine(content);
        content.moveTo(PAGE_MARGIN, 495);
        content.lineTo(PAGE_MARGIN + CONTENT_WIDTH, 495);
        content.stroke();

        setGreen(content);
        drawText(content, BOLD, 9, PAGE_MARGIN, 476, "ACTIVE FILTERS");
        setInk(content);
        List<String> filterLines = wrapText(formatFilters(filters), REGULAR, 9, CONTENT_WIDTH);
        float filterY = 459;
        for (String line : filterLines) {
            drawText(content, REGULAR, 9, PAGE_MARGIN, filterY, line);
            filterY -= 13;
        }

        float cardsTop = filterY - 8;
        float cardsBottom = cardsTop - 50;
        drawSummaryCards(content, rows, cardsBottom);
        setInk(content);
        drawText(content, BOLD, 12, PAGE_MARGIN, cardsBottom - 24,
                "Matching properties  (" + rows.size() + ")");
        return cardsBottom - 42;
    }

    private static float drawContinuationHeader(PDPageContentStream content) throws IOException {
        setGreen(content);
        drawText(content, BOLD, 9, PAGE_MARGIN, 570, "HEARTH & METRIC  /  MARKET ANALYSIS");
        setInk(content);
        drawText(content, BOLD, 18, PAGE_MARGIN, 538, "Matching properties - continued");
        setLine(content);
        content.moveTo(PAGE_MARGIN, 522);
        content.lineTo(PAGE_MARGIN + CONTENT_WIDTH, 522);
        content.stroke();
        return 507;
    }

    private static void drawSummaryCards(PDPageContentStream content, List<MarketProperty> rows,
                                         float bottom) throws IOException {
        List<Double> prices = rows.stream().map(MarketProperty::price).sorted().toList();
        String average = prices.isEmpty() ? "-" : formatCurrency(
                prices.stream().mapToDouble(Double::doubleValue).average().orElseThrow());
        // Even-sized samples use the mean of the two central values; odd samples use the center.
        String median = prices.isEmpty() ? "-" : formatCurrency(prices.size() % 2 == 0
                ? (prices.get(prices.size() / 2 - 1) + prices.get(prices.size() / 2)) / 2
                : prices.get(prices.size() / 2));
        String range = prices.isEmpty() ? "-" : formatCurrency(prices.getFirst()) + " - "
                + formatCurrency(prices.getLast());
        List<SummaryValue> values = List.of(
                new SummaryValue("MATCHING HOMES", Integer.toString(rows.size())),
                new SummaryValue("AVERAGE PRICE", average),
                new SummaryValue("MEDIAN PRICE", median),
                new SummaryValue("PRICE RANGE", range));

        float gap = 8;
        float width = (CONTENT_WIDTH - gap * 3) / 4;
        for (int index = 0; index < values.size(); index++) {
            float x = PAGE_MARGIN + index * (width + gap);
            boolean green = index % 2 == 0;
            if (green) {
                setGreen(content);
            } else {
                content.setNonStrokingColor(244 / 255f, 223 / 255f, 199 / 255f);
            }
            content.addRect(x, bottom, width, 50);
            content.fill();
            if (green) {
                content.setNonStrokingColor(1f, 1f, 1f);
            } else {
                setInk(content);
            }
            drawText(content, BOLD, 7, x + 10, bottom + 33, values.get(index).label());
            drawText(content, BOLD, index == 3 ? 11 : 14, x + 10, bottom + 12,
                    values.get(index).value());
        }
    }

    private static int drawTable(PDPageContentStream content, List<MarketProperty> rows,
                                 int startIndex, float tableTop) throws IOException {
        drawTableHeader(content, tableTop);
        if (rows.isEmpty()) {
            setMuted(content);
            drawText(content, REGULAR, 11, PAGE_MARGIN + 12, tableTop - 48,
                    "No matching data for the selected filters.");
            return 0;
        }

        int rowIndex = startIndex;
        float rowTop = tableTop - TABLE_HEADER_HEIGHT;
        // Reserve 42 points for the footer and stop before the next row would overlap it.
        while (rowIndex < rows.size() && rowTop - TABLE_ROW_HEIGHT >= 42) {
            float rowBottom = rowTop - TABLE_ROW_HEIGHT;
            if ((rowIndex - startIndex) % 2 == 1) {
                content.setNonStrokingColor(247 / 255f, 244 / 255f, 237 / 255f);
                content.addRect(PAGE_MARGIN, rowBottom, CONTENT_WIDTH, TABLE_ROW_HEIGHT);
                content.fill();
            }
            drawTableRow(content, rows.get(rowIndex), rowBottom);
            setLine(content);
            content.moveTo(PAGE_MARGIN, rowBottom);
            content.lineTo(PAGE_MARGIN + CONTENT_WIDTH, rowBottom);
            content.stroke();
            rowTop = rowBottom;
            rowIndex++;
        }
        return rowIndex;
    }

    private static void drawTableHeader(PDPageContentStream content, float tableTop)
            throws IOException {
        setGreen(content);
        content.addRect(PAGE_MARGIN, tableTop - TABLE_HEADER_HEIGHT, CONTENT_WIDTH,
                TABLE_HEADER_HEIGHT);
        content.fill();
        content.setNonStrokingColor(1f, 1f, 1f);
        float x = PAGE_MARGIN;
        for (Column column : TABLE_COLUMNS) {
            drawText(content, BOLD, 7, x + 7, tableTop - 15, column.label());
            x += column.width();
        }
    }

    private static void drawTableRow(PDPageContentStream content, MarketProperty row,
                                     float bottom) throws IOException {
        List<String> values = List.of(
                Integer.toString(row.id()), formatNumber(row.squareFootage()) + " sq ft",
                Integer.toString(row.bedrooms()), formatNumber(row.bathrooms()),
                Integer.toString(row.yearBuilt()), formatNumber(row.lotSize()),
                formatNumber(row.schoolRating()),
                formatNumber(row.distanceToCityCenter()) + " mi", formatCurrency(row.price()));
        setInk(content);
        float x = PAGE_MARGIN;
        for (int index = 0; index < TABLE_COLUMNS.size(); index++) {
            drawText(content, index == TABLE_COLUMNS.size() - 1 ? BOLD : REGULAR, 8,
                    x + 7, bottom + 6, values.get(index));
            x += TABLE_COLUMNS.get(index).width();
        }
    }

    private static void drawFooter(PDPageContentStream content, int pageNumber)
            throws IOException {
        setMuted(content);
        drawText(content, REGULAR, 7, PAGE_MARGIN, 20,
                "Housing Market Export  |  Technical demonstration - not an appraisal");
        drawText(content, BOLD, 7, PAGE_MARGIN + CONTENT_WIDTH - 42, 20,
                "Page " + pageNumber);
    }

    private static String formatFilters(Map<String, Number> filters) {
        if (filters.isEmpty()) {
            return "None - showing all supplied records";
        }
        List<String> values = new ArrayList<>();
        // Iterate the allowlisted definitions so labels and display order do not depend on map order.
        for (FilterDefinition definition : FILTER_DEFINITIONS) {
            Number value = filters.get(definition.key());
            if (value != null) {
                values.add(definition.label() + ": " + formatFilterValue(value, definition.type()));
            }
        }
        return String.join("   |   ", values);
    }

    private static String formatFilterValue(Number value, FilterType type) {
        // A switch expression must cover every enum constant and directly yields the formatted value.
        return switch (type) {
            case CURRENCY -> formatCurrency(value.doubleValue());
            case AREA -> formatNumber(value.doubleValue()) + " sq ft";
            case DISTANCE -> formatNumber(value.doubleValue()) + " mi";
            case NUMBER -> formatNumber(value.doubleValue());
        };
    }

    private static String formatCurrency(double value) {
        return new DecimalFormat("$#,##0", DecimalFormatSymbols.getInstance(Locale.US))
                .format(value);
    }

    private static String formatNumber(double value) {
        return new DecimalFormat("#,##0.##", DecimalFormatSymbols.getInstance(Locale.US))
                .format(value);
    }

    private static List<String> wrapText(String text, PDFont font, float fontSize,
                                         float maxWidth) throws IOException {
        List<String> lines = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        for (String word : text.split(" ")) {
            String candidate = current.isEmpty() ? word : current + " " + word;
            // PDF font widths use 1/1000 text-space units and must be scaled by the font size.
            float width = font.getStringWidth(candidate) / 1000 * fontSize;
            if (width > maxWidth && !current.isEmpty()) {
                lines.add(current.toString());
                current = new StringBuilder(word);
            } else {
                current = new StringBuilder(candidate);
            }
        }
        if (!current.isEmpty()) {
            lines.add(current.toString());
        }
        return lines;
    }

    private static void drawText(PDPageContentStream content, PDFont font, float fontSize,
                                 float x, float y, String text) throws IOException {
        content.beginText();
        content.setFont(font, fontSize);
        content.newLineAtOffset(x, y);
        // Standard Type 1 fonts support printable ASCII only; replace unsupported glyphs safely.
        content.showText(text.replaceAll("[^\\x20-\\x7E]", "?"));
        content.endText();
    }

    private static void setGreen(PDPageContentStream content) throws IOException {
        content.setNonStrokingColor(35 / 255f, 91 / 255f, 69 / 255f);
    }

    private static void setInk(PDPageContentStream content) throws IOException {
        content.setNonStrokingColor(20 / 255f, 35 / 255f, 29 / 255f);
    }

    private static void setMuted(PDPageContentStream content) throws IOException {
        content.setNonStrokingColor(95 / 255f, 109 / 255f, 102 / 255f);
    }

    private static void setLine(PDPageContentStream content) throws IOException {
        content.setStrokingColor(217 / 255f, 221 / 255f, 213 / 255f);
        content.setLineWidth(.6f);
    }

    // Small private records make layout metadata immutable without exposing it as API state.
    private record Column(String label, float width) {
    }

    private record FilterDefinition(String key, String label, FilterType type) {
    }

    private enum FilterType {
        CURRENCY, AREA, DISTANCE, NUMBER
    }

    private record SummaryValue(String label, String value) {
    }

    public static class ExportFailedException extends RuntimeException {
        public ExportFailedException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
